"""Read-only Cloudflare R2 connectivity and dataset-access verification."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

from .config import Settings, settings

REQUIRED_FIELDS = (
    "R2_ENABLED",
    "R2_ACCOUNT_ID",
    "R2_BUCKET",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_ENDPOINT_URL",
)
R2_ENDPOINT_PATTERN = re.compile(
    r"^https://[a-zA-Z0-9-]+\.r2\.cloudflarestorage\.com/?$"
)
EXPECTED_METADATA = (
    "groups.csv",
    "dataset-source.json",
    "train.csv",
    "val.csv",
    "test.csv",
    "report.json",
    "dataset-card.json",
)
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")


class R2VerificationError(RuntimeError):
    """Raised when local R2 configuration cannot be verified safely."""


def normalize_prefix(value: str, *, bucket: str = "") -> str:
    """Validate and normalize an object prefix without allowing traversal."""

    prefix = value.strip().replace("\\", "/").strip("/")
    bucket_name = bucket.strip().replace("\\", "/").strip("/")
    if bucket_name and prefix.startswith(f"{bucket_name}/"):
        prefix = prefix[len(bucket_name) + 1 :]
    if not prefix or ".." in prefix.split("/"):
        raise ValueError("R2 dataset prefixes must be non-empty and contain no '..'")
    if prefix.startswith("/"):
        raise ValueError("R2 dataset prefixes must not start with '/'")
    return f"{prefix}/"


@dataclass(frozen=True)
class PrefixResult:
    prefix: str
    accessible: bool
    object_names: tuple[str, ...]
    error: str | None = None
    metadata_files: tuple[str, ...] = ()
    label_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class VerificationResult:
    configuration_valid: bool
    bucket_reachable: bool
    bucket_status: str
    prefixes: tuple[PrefixResult, ...]


def dataset_prefixes(config: Settings = settings) -> dict[str, str]:
    return {
        "forgerynet": normalize_prefix(
            config.r2_forgerynet_prefix, bucket=config.r2_bucket
        ),
        "cifake": normalize_prefix(config.r2_cifake_prefix, bucket=config.r2_bucket),
    }


def validate_configuration(config: Settings = settings) -> None:
    if not config.r2_enabled:
        raise R2VerificationError("R2_ENABLED must be true for connectivity verification.")
    values = {
        "R2_ACCOUNT_ID": config.r2_account_id,
        "R2_BUCKET": config.r2_bucket,
        "R2_ACCESS_KEY_ID": config.r2_access_key_id,
        "R2_SECRET_ACCESS_KEY": config.r2_secret_access_key,
        "R2_ENDPOINT_URL": config.r2_endpoint_url,
    }
    missing = [name for name, value in values.items() if not value.strip()]
    if missing:
        raise R2VerificationError(f"Missing required R2 configuration: {', '.join(missing)}")
    if not R2_ENDPOINT_PATTERN.fullmatch(config.r2_endpoint_url):
        raise R2VerificationError(
            "R2_ENDPOINT_URL must use https://<account>.r2.cloudflarestorage.com"
        )
    endpoint_account = config.r2_endpoint_url.split("//", 1)[1].split(".", 1)[0]
    if endpoint_account != config.r2_account_id:
        raise R2VerificationError("R2 endpoint account does not match R2_ACCOUNT_ID.")
    try:
        dataset_prefixes(config)
    except ValueError as exc:
        raise R2VerificationError(str(exc)) from exc


def _error_status(exc: ClientError) -> str:
    code = str(exc.response.get("Error", {}).get("Code", ""))
    status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if code in {"InvalidAccessKeyId", "SignatureDoesNotMatch"}:
        return "invalid credentials"
    if code in {"NoSuchBucket", "404"} or status == 404:
        return "bucket not found"
    if code in {"AccessDenied", "403"} or status == 403:
        return "permission denied for bucket access"
    return "R2 service error"


def _inspect_prefix(client: Any, bucket: str, prefix: str) -> PrefixResult:
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=20)
        names = tuple(item["Key"] for item in response.get("Contents", [])[:20])
    except EndpointConnectionError:
        return PrefixResult(prefix, False, (), "connection/network failure")
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        message = (
            "permission denied for dataset listing"
            if code in {"AccessDenied", "403"}
            else _error_status(exc)
        )
        return PrefixResult(prefix, False, (), message)
    metadata = tuple(
        expected
        for expected in EXPECTED_METADATA
        if any(name.rstrip("/").endswith(f"/{expected}") or name.rstrip("/") == f"{prefix}{expected}".rstrip("/") for name in names)
    )
    label_counts = tuple(
        (label, sum(1 for name in names if f"/{label}/" in f"/{name}" and name.lower().endswith(IMAGE_SUFFIXES)))
        for label in ("real", "fake")
    )
    return PrefixResult(prefix, True, names, metadata_files=metadata, label_counts=label_counts)


def verify_r2(
    config: Settings = settings,
    *,
    client: Any | None = None,
    selected_datasets: tuple[str, ...] = ("forgerynet", "cifake"),
) -> VerificationResult:
    validate_configuration(config)
    prefixes = dataset_prefixes(config)
    unknown = set(selected_datasets) - set(prefixes)
    if unknown:
        raise R2VerificationError(f"Unknown dataset(s): {', '.join(sorted(unknown))}")
    if client is None:
        client = boto3.client(
            "s3",
            endpoint_url=config.r2_endpoint_url,
            region_name="auto",
            aws_access_key_id=config.r2_access_key_id,
            aws_secret_access_key=config.r2_secret_access_key,
        )
    try:
        client.head_bucket(Bucket=config.r2_bucket)
    except NoCredentialsError as exc:
        raise R2VerificationError("invalid credentials: boto3 could not find credentials") from exc
    except EndpointConnectionError as exc:
        raise R2VerificationError("connection/network failure while reaching R2") from exc
    except ClientError as exc:
        raise R2VerificationError(_error_status(exc)) from exc
    results = tuple(
        _inspect_prefix(client, config.r2_bucket, prefixes[name]) for name in selected_datasets
    )
    return VerificationResult(True, True, "reachable", results)


def _print_result(result: VerificationResult) -> None:
    print("R2 configuration: valid")
    print(f"Bucket connection: {result.bucket_status}")
    for item in result.prefixes:
        if not item.accessible:
            print(f"{item.prefix}: inaccessible ({item.error})")
            continue
        state = "empty" if not item.object_names else "accessible"
        print(f"{item.prefix}: {state} ({len(item.object_names)} object(s), max 20)")
        for name in item.object_names:
            print(f"  {name}")
        if item.label_counts:
            print("  likely image counts in sample: " + ", ".join(f"{k}={v}" for k, v in item.label_counts))
        print("  expected metadata: " + ", ".join(
            f"{name}={'present' if name in item.metadata_files else 'missing'}"
            for name in EXPECTED_METADATA
        ))
    if all(item.accessible and not item.object_names for item in result.prefixes):
        print("R2 connection works, but the selected dataset prefixes are empty.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--dataset", choices=("forgerynet", "cifake"))
    selection.add_argument("--all-datasets", action="store_true")
    args = parser.parse_args()
    selected = (args.dataset,) if args.dataset else ("forgerynet", "cifake")
    try:
        _print_result(verify_r2(selected_datasets=selected))
    except R2VerificationError as exc:
        print(f"R2 verification failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
