from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Frequency-Aware Deepfake Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "frequency-aware-deepfake-detector",
        "version": "0.1.0",
    }


@app.post("/predict")
def predict() -> dict:
    return {
        "status": "pending",
        "message": "Model inference is not implemented yet.",
    }
