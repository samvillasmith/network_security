from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from network_security.explainer import PredictionExplainer
from network_security.feature_dictionary import FEATURE_NAMES
from network_security.url_features import REPUTATION_DEFAULTS, extract_features
from utils.main_utils.utils import load_numpy_array_data, load_object


def _find_latest_model() -> Path:
    candidates = sorted(
        Path("artifacts").glob("*/model_trainer/trained_model/model.pkl")
    )
    if not candidates:
        raise RuntimeError(
            "No trained model found under artifacts/. Run `python main.py` first."
        )
    return candidates[-1]


def _background_data_for(model_path: Path) -> np.ndarray:
    artifact_root = model_path.parents[2]
    train_arr_path = artifact_root / "data_transformation" / "transformed" / "train.npy"
    if not train_arr_path.exists():
        raise RuntimeError(
            f"Background data not found at {train_arr_path}. "
            "Re-run `python main.py` so the trained model and transformed data stay in sync."
        )
    arr = load_numpy_array_data(str(train_arr_path))
    return arr[:, :-1]


MODEL_PATH = _find_latest_model()
network_model = load_object(str(MODEL_PATH))
explainer = PredictionExplainer(network_model, _background_data_for(MODEL_PATH))
INDEX_HTML = Path("static/index.html")

app = FastAPI(title="Phishing URL Classifier", version="1.0.0")


class PredictRequest(BaseModel):
    features: dict[str, float] = Field(
        description="Feature vector keyed by feature name. All 30 features required."
    )


class TopFeature(BaseModel):
    feature: str
    input_value: float
    shap_contribution: float


class PredictResponse(BaseModel):
    label: str
    phishing_probability: float
    explanation: str
    top_features: list[TopFeature]


class AnalyzeRequest(BaseModel):
    url: str = Field(description="A URL to fetch, featurize, and classify.")


class AnalyzeResponse(BaseModel):
    url: str
    features: dict[str, float]
    reputation_feature_names: list[str]
    prediction: PredictResponse


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML.read_text(encoding="utf-8")


@app.get("/api/status")
def status():
    return {
        "status": "ready",
        "model_path": str(MODEL_PATH),
        "expected_features": FEATURE_NAMES,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    missing = [f for f in FEATURE_NAMES if f not in req.features]
    if missing:
        raise HTTPException(status_code=400, detail={"missing_features": missing})
    return explainer.predict_and_explain(req.features)


@app.post("/analyze_url", response_model=AnalyzeResponse)
def analyze_url(req: AnalyzeRequest):
    features = extract_features(req.url)
    prediction = explainer.predict_and_explain(features)
    return AnalyzeResponse(
        url=req.url,
        features=features,
        reputation_feature_names=list(REPUTATION_DEFAULTS.keys()),
        prediction=prediction,
    )
