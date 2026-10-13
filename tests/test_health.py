import io
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get('/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'service' in payload


def test_predict_image_endpoint():
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(dummy, (100, 100), 40, (255, 200, 150), -1)
    _, buf = cv2.imencode('.jpg', dummy)

    files = {'file': ('test.jpg', io.BytesIO(buf.tobytes()), 'image/jpeg')}
    response = client.post('/predict', files=files)
    assert response.status_code == 200
    data = response.json()
    assert 'verdict' in data
    assert 'confidence_pct' in data
    assert 'visualizations' in data
    assert 'face_crop' in data['visualizations']
    assert 'fft_spectrum' in data['visualizations']
    assert 'dwt_subbands' in data['visualizations']
