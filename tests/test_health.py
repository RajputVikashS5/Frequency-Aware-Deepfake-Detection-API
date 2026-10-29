import io
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import forensics

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get('/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'service' in payload
    assert payload['inference_available'] is False


def test_analyze_image_endpoint_returns_diagnostic_only_response():
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(dummy, (100, 100), 40, (255, 200, 150), -1)
    _, buf = cv2.imencode('.jpg', dummy)

    files = {'file': ('test.jpg', io.BytesIO(buf.tobytes()), 'image/jpeg')}
    response = client.post('/api/v1/analyze', files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "diagnostic_complete"
    assert data["inference_available"] is False
    assert data["model_version"] is None
    assert "is_fake" not in data
    assert "confidence_pct" not in data
    assert "calibrated_score" not in data
    assert "not a deepfake classification" in data["message"]
    diagnostic_text = " ".join(data["findings"]).lower()
    assert not any(term in diagnostic_text for term in ("verdict", "score", "confidence", "authentic", "generative"))
    assert 'visualizations' in data
    assert 'face_crop' in data['visualizations']
    assert 'fft_spectrum' in data['visualizations']
    assert 'dwt_subbands' in data['visualizations']


def test_predict_compatibility_alias_is_diagnostic_only():
    response = client.post('/predict', files={'file': ('test.png', io.BytesIO(b''), 'image/png')})
    assert response.status_code == 400
    assert response.json()["detail"]


def test_face_detection_falls_back_when_cascade_is_empty(monkeypatch):
    class EmptyCascade:
        def empty(self):
            return True

    monkeypatch.setattr(forensics.cv2, "CascadeClassifier", lambda _: EmptyCascade())
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    crop, found, bbox = forensics.detect_and_crop_face(image)
    assert crop.shape == (256, 256, 3)
    assert found is False
    assert bbox["w"] == 32
