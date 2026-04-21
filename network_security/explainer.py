from typing import Any

import anthropic
import numpy as np
import shap

from network_security.feature_dictionary import FEATURE_DICTIONARY, FEATURE_NAMES


MODEL = "claude-sonnet-4-6"
TOP_K_FEATURES = 5
MAX_TOKENS = 400

# Target encoding: training pipeline maps UCI's {-1: phishing, 1: legitimate} via
# replace(-1, 0), so class 0 = phishing and class 1 = legitimate.
PHISHING_CLASS = 0

SYSTEM_PROMPT = f"""You are a security analyst who explains phishing-URL classifier predictions to non-experts.

You will receive the classifier's output (label and phishing probability) plus the top SHAP-ranked features that drove the decision. Write a concise 2-3 sentence plain-English explanation of why the URL was classified that way, grounded only in the features provided. Do not invent signals that weren't supplied. Avoid jargon like "SHAP" or "model weights"; refer to features by what they measure.

Feature dictionary:

{FEATURE_DICTIONARY}
Output format: the explanation paragraph only. No preamble, no headers, no bullet lists.
"""


class PredictionExplainer:
    def __init__(self, network_model, background_data):
        self.model = network_model.model
        self.preprocessor = network_model.preprocessor
        masker = shap.maskers.Independent(background_data, max_samples=100)
        self._shap_explainer = shap.Explainer(self.model, masker)
        self._ = anthropic.Anthropic()

    def predict_and_explain(self, features: dict[str, float]) -> dict[str, Any]:
        x = np.array([[features[name] for name in FEATURE_NAMES]], dtype=float)
        x_t = self.preprocessor.transform(x)

        pred = int(self.model.predict(x_t)[0])
        proba = float(self.model.predict_proba(x_t)[0][PHISHING_CLASS])
        label = "phishing" if pred == PHISHING_CLASS else "legitimate"

        contributions = self._rank_contributions(x_t, features)
        explanation = self._call_claude(label, proba, contributions)

        return {
            "label": label,
            "phishing_probability": proba,
            "explanation": explanation,
            "top_features": contributions,
        }

    def _rank_contributions(self, x_t, features):
        arr = np.asarray(self._shap_explainer(x_t).values)
        if arr.ndim == 3:
            arr = arr[0, :, PHISHING_CLASS] if arr.shape[0] == 1 else arr[PHISHING_CLASS][0]
        elif arr.ndim == 2:
            arr = arr[0]

        ranked = sorted(
            zip(FEATURE_NAMES, arr),
            key=lambda kv: abs(float(kv[1])),
            reverse=True,
        )[:TOP_K_FEATURES]
        return [
            {
                "feature": name,
                "input_value": features[name],
                "shap_contribution": float(val),
            }
            for name, val in ranked
        ]

    def _call_claude(self, label, proba, contributions):
        bullets = "\n".join(
            f"- {c['feature']} = {c['input_value']} "
            f"(contribution: {c['shap_contribution']:+.3f} toward phishing)"
            for c in contributions
        )
        user_message = (
            f"Classifier prediction: {label} (phishing probability = {proba:.3f}).\n\n"
            f"Top {len(contributions)} contributing features:\n{bullets}\n\n"
            "Positive contributions pushed the model toward 'phishing'; "
            "negative contributions pushed toward 'legitimate'."
        )

        response = self._.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "disabled"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        return next(b.text for b in response.content if b.type == "text").strip()
