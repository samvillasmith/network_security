from pathlib import Path

import numpy as np
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from network_security.explainer import PredictionExplainer
from network_security.url_features import (
    REPUTATION_DEFAULTS,
    UnsafeURLError,
    extract_features,
)
from utils.main_utils.utils import load_numpy_array_data, load_object


st.set_page_config(page_title="Phishing URL Classifier", layout="wide")


@st.cache_resource
def load_explainer():
    model_path = sorted(
        Path("artifacts").glob("*/model_trainer/trained_model/model.pkl")
    )[-1]
    network_model = load_object(str(model_path))
    train_path = (
        model_path.parents[2] / "data_transformation" / "transformed" / "train.npy"
    )
    background = load_numpy_array_data(str(train_path))[:, :-1]
    return PredictionExplainer(network_model, background), model_path


explainer, model_path = load_explainer()

st.title("Phishing URL Classifier")
st.caption(
    f"Gradient Boosting classifier + Claude Sonnet 4.6 explanation. "
    f"Model: `{model_path}`"
)

url = st.text_input(
    "URL to analyze",
    placeholder="https://example.com",
)
analyze = st.button("Analyze URL", type="primary", disabled=not url)

if analyze and url:
    try:
        with st.spinner("Fetching, WHOIS, DNS, extracting features..."):
            features = extract_features(url)
    except UnsafeURLError as e:
        st.error(f"Refused to analyze URL: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Extraction failed: {e}")
        st.stop()

    with st.spinner("Scoring and asking Sonnet 4.6 for an explanation..."):
        pred = explainer.predict_and_explain(features)

    prob = pred["phishing_probability"]
    if pred["label"] == "phishing":
        st.error(f"### PHISHING  —  P(phishing) = {prob:.1%}")
    else:
        st.success(f"### LEGITIMATE  —  P(phishing) = {prob:.1%}")
    st.progress(prob)

    st.subheader("Explanation")
    st.write(pred["explanation"])

    st.subheader("Top contributing features")
    for t in pred["top_features"]:
        c = t["shap_contribution"]
        arrow = "↑ phishing" if c >= 0 else "↓ phishing"
        st.markdown(
            f"- `{t['feature']}` = **{int(t['input_value']):+d}**  "
            f"→ {c:+.3f}  _{arrow}_"
        )

    with st.expander(f"All 30 extracted features"):
        st.caption(
            "Reputation features (traffic rank, PageRank, Google index, inbound "
            "links, blocklist status) default to 0 — they require paid external APIs."
        )
        cols = st.columns(3)
        for i, (name, val) in enumerate(features.items()):
            is_default = name in REPUTATION_DEFAULTS
            suffix = " *(default)*" if is_default else ""
            cols[i % 3].markdown(f"`{name}` = **{int(val):+d}**{suffix}")
