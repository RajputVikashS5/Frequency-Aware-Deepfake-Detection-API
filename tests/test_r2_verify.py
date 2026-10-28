from dataclasses import replace

import pytest
from botocore.exceptions import ClientError

from backend.app.config import Settings
from backend.app import r2_verify
from backend.app.r2_verify import R2VerificationError, dataset_prefixes, verify_r2


def config(**changes):
    return replace(
        Settings(
            r2_enabled=True,
            r2_account_id="account123",
            r2_bucket="deepfake",
            r2_access_key_id="access",
            r2_secret_access_key="secret",
            r2_endpoint_url="https://account123.r2.cloudflarestorage.com",
        ),
        **changes,
    )


class ReadOnlyClient:
    def __init__(self, contents=None):
        self.contents = contents or {}
        self.calls = []

    def head_bucket(self, **kwargs):
        self.calls.append(("head_bucket", kwargs))

    def list_objects_v2(self, **kwargs):
        self.calls.append(("list_objects_v2", kwargs))
        return {"Contents": [{"Key": key} for key in self.contents.get(kwargs["Prefix"], [])]}


def client_error(code, status):
    return ClientError(
        {"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "operation",
    )


def test_valid_read_only_access_lists_at_most_twenty_objects():
    client = ReadOnlyClient(
        {
            "faceforensics++/": ["faceforensics++/original/000.mp4"],
            "CIfake/": ["CIfake/train.csv"],
        }
    )

    result = verify_r2(config(), client=client)

    assert result.bucket_reachable is True
    assert result.prefixes[0].object_names == (
        "faceforensics++/original/000.mp4",
    )
    assert all(call[0] != "put_object" for call in client.calls)
    assert all(call[0] != "delete_object" for call in client.calls)
    assert all(call[1].get("MaxKeys") == 20 for call in client.calls if call[0] == "list_objects_v2")
    assert client.calls[0] == ("head_bucket", {"Bucket": "deepfake"})
    assert all(call[1]["Bucket"] == "deepfake" for call in client.calls)


def test_default_dataset_prefixes_are_bucket_relative():
    prefixes = dataset_prefixes(config())

    assert prefixes == {
        "faceforensicspp": "faceforensics++/",
        "cifake": "CIfake/",
    }
    assert all(not prefix.startswith("deepfake/") for prefix in prefixes.values())


def test_dataset_cli_accepts_faceforensicspp(monkeypatch):
    captured = {}

    def fake_verify_r2(*, selected_datasets):
        captured["selected_datasets"] = selected_datasets
        return object()

    monkeypatch.setattr(r2_verify, "verify_r2", fake_verify_r2)
    monkeypatch.setattr(r2_verify, "_print_result", lambda result: None)
    monkeypatch.setattr(
        "sys.argv", ["r2_verify", "--dataset", "faceforensicspp"]
    )

    assert r2_verify.main() == 0
    assert captured["selected_datasets"] == ("faceforensicspp",)


def test_missing_configuration_fails_without_client_calls():
    with pytest.raises(R2VerificationError, match="R2_ENABLED"):
        verify_r2(replace(config(), r2_enabled=False), client=ReadOnlyClient())


def test_invalid_credentials_are_distinguished():
    class Client:
        def head_bucket(self, **kwargs):
            raise client_error("InvalidAccessKeyId", 403)

    with pytest.raises(R2VerificationError, match="invalid credentials"):
        verify_r2(config(), client=Client())


def test_access_denied_is_distinguished():
    class Client:
        def head_bucket(self, **kwargs):
            raise client_error("AccessDenied", 403)

    with pytest.raises(R2VerificationError, match="permission denied"):
        verify_r2(config(), client=Client())


def test_bucket_not_found_is_distinguished():
    class Client:
        def head_bucket(self, **kwargs):
            raise client_error("NoSuchBucket", 404)

    with pytest.raises(R2VerificationError, match="bucket not found"):
        verify_r2(config(), client=Client())


def test_empty_prefix_is_accessible_but_empty():
    result = verify_r2(config(), client=ReadOnlyClient())

    assert all(item.accessible for item in result.prefixes)
    assert all(item.object_names == () for item in result.prefixes)
