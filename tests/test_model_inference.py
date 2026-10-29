import io

import numpy as np
import torch
from PIL import Image

from backend.app import model_inference


class BiasedModel(torch.nn.Module):
    def __init__(self, logits=(4.0, -4.0)):
        super().__init__()
        self.logits = torch.nn.Parameter(torch.tensor(logits))

    def forward(self, image):
        return self.logits.expand(image.shape[0], -1)


def _image_bytes(size: int) -> bytes:
    image = Image.fromarray(np.full((size, size, 3), 127, dtype=np.uint8), "RGB")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _write_checkpoint(path, *, task="forgerynet", threshold=0.5, temperature=1.0):
    torch.save(
        {
            "model_state": BiasedModel().state_dict(),
            "config": {
                "task": task,
                "label_semantics": "manipulated_vs_real",
                "score_type": "raw probability",
                "threshold": threshold,
                "temperature": temperature,
                "uncertainty_band": [0.35, 0.65],
                "training_resolution": 32,
            },
        },
        path,
    )


def test_class_zero_bias_returns_likely_real(tmp_path, monkeypatch):
    checkpoint = tmp_path / "model.pt"
    _write_checkpoint(checkpoint)
    monkeypatch.setattr(model_inference, "build_model", lambda pretrained=False: BiasedModel())

    inference = model_inference.RGBBaselineInference(str(checkpoint))
    result = inference.predict(_image_bytes(32))

    assert result.prediction == "likely_real"
    assert result.score < 0.5


def test_cifake_checkpoint_is_inconclusive_for_high_resolution_upload(tmp_path, monkeypatch):
    checkpoint = tmp_path / "cifake.pt"
    _write_checkpoint(checkpoint, task="cifake")
    monkeypatch.setattr(model_inference, "build_model", lambda pretrained=False: BiasedModel(( -4.0, 4.0)))

    inference = model_inference.RGBBaselineInference(str(checkpoint))
    result = inference.predict(_image_bytes(1024))

    assert result.prediction == "inconclusive"
    assert "32x32" in (result.reason or "")


def test_threshold_and_temperature_are_loaded_from_checkpoint(tmp_path, monkeypatch):
    checkpoint = tmp_path / "calibrated.pt"
    _write_checkpoint(checkpoint, threshold=0.99, temperature=2.0)
    monkeypatch.setattr(model_inference, "build_model", lambda pretrained=False: BiasedModel((-4.0, 4.0)))

    inference = model_inference.RGBBaselineInference(str(checkpoint))
    result = inference.predict(_image_bytes(32))

    assert inference.threshold == 0.99
    assert inference.temperature == 2.0
    assert result.prediction == "likely_real"
