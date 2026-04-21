# Network Security — Phishing URL Classifier

End-to-end ML pipeline that trains a binary classifier on network/phishing-URL
features pulled from MongoDB, produces a serialized model, and serves it via
FastAPI and Streamlit with SHAP-based explainability and Claude-generated
plain-English explanations.

## Architecture

```
MongoDB ─► DataIngestion ─► DataValidation ─► DataTransformation ─► ModelTrainer ─► model.pkl
                                                                                       │
                                                         ┌────────────────────────────────┘
                                                         ▼
                                              FastAPI / Streamlit serving
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                        /predict              /analyze_url
                                     (manual features)     (auto-extract from URL)
                                              │                     │
                                              └──────────┬──────────┘
                                                         ▼
                                              SHAP explanation + Claude Sonnet
                                              natural-language summary
```

## Pipeline stages

1. **Data ingestion** (`network_security/components/data_ingestion.py`)
   Pulls the `NetworkData` collection from MongoDB, writes it to a feature
   store CSV, and produces a train/test split (80/20) on disk.

2. **Data validation** (`network_security/components/data_validation.py`)
   Checks column count against `data_schema/schema.yaml` and runs a
   Kolmogorov-Smirnov drift test between train and test distributions. Writes
   a drift report to YAML.

3. **Data transformation** (`network_security/components/data_transformation.py`)
   Imputes missing values with a `KNNImputer` (3 neighbors, uniform weights),
   remaps the `Result` label from `{-1, 1}` to `{0, 1}`, and saves
   transformed train/test numpy arrays plus the fitted preprocessor.

4. **Model trainer** (`network_security/model_trainer.py`)
   Evaluates five candidate classifiers via GridSearchCV, selects the best on
   a validation split, enforces quality gates, and saves the final model.

Every stage is orchestrated from `main.py` and produces a typed artifact
(`network_security/entity/artifact_entity.py`) that the next stage consumes.

## Model training

Five candidate classifiers are evaluated:

- Logistic Regression
- Decision Tree
- AdaBoost
- Gradient Boosting
- Random Forest

### How the winner is chosen

The transformed training set is split into **train / validation** (80/20,
stratified, `random_state=42`). For each candidate, `GridSearchCV` (3-fold,
scoring=`f1`) sweeps a hyper-parameter grid on the training fold. The
candidate with the highest **validation** F1 is selected. Final metrics
reported on the artifact are computed on the untouched **test** set.

### Quality gates

Before saving, two gates must pass or the pipeline raises:

- `test_f1 >= MODEL_TRAINER_EXPECTED_SCORE` (default `0.6`)
- `|train_f1 - test_f1| <= MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD`
  (default `0.05`)

### Experiment tracking

Every candidate run and the final selection are logged to MLflow as nested
runs under a parent `model_selection` run (experiment name `NetworkSecurity`).
By default this writes to a local `./mlruns/` directory.

```bash
mlflow ui
```

## Serving & explainability

### FastAPI (`app.py`)

Serves the trained model with two prediction endpoints:

- **`POST /predict`** — accepts a 30-feature vector manually, returns label,
  phishing probability, SHAP-ranked top features, and a Claude-generated
  plain-English explanation.
- **`POST /analyze_url`** — accepts a raw URL, auto-extracts all 30 features
  (HTTP fetch, WHOIS, DNS, HTML parsing), classifies, and explains.
- **`GET /`** — serves an interactive single-page UI (`static/index.html`)
  with preset loaders, per-feature toggle controls, and a URL analysis bar.

```bash
uvicorn app:app --reload
```

### Streamlit (`streamlit_app.py`)

Alternative UI with the same analyze-URL workflow.

```bash
streamlit run streamlit_app.py
```

### Explainability (`network_security/explainer.py`)

Uses **SHAP** (with `shap.Explainer` and an `Independent` masker on training
background data) to rank the top 5 contributing features for each prediction.
The SHAP contributions plus the prediction are then sent to **Claude Sonnet**
via the Anthropic API to generate a concise, jargon-free explanation of why
the URL was classified as phishing or legitimate.

### URL feature extraction (`network_security/url_features.py`)

Extracts 30 features from a live URL using:

- **URL structure parsing** — IP detection, length, shortener check, `@`
  symbol, subdomain count, HTTPS token in domain, non-standard ports
- **HTTP fetch** — SSL certificate validation, redirect counting
- **WHOIS** — domain age, registration length, abnormal URL detection
- **DNS** — record existence check
- **HTML content analysis** — favicon origin, external resource fraction,
  anchor analysis, form handler targets, mailto submission, JS behavior
  (mouseover status bar, right-click disable, popups, hidden iframes)

Five reputation features (web traffic, PageRank, Google Index, inbound links,
blocklist status) default to 0 as they require paid external APIs.

**Safety:** The URL fetcher blocks requests to localhost, private/reserved IP
ranges, and other internal addresses to prevent SSRF.

## Setup

Requires Python 3.10+ and a MongoDB instance populated with the
`NetworkSecurity.NetworkData` collection.

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# or: .venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
ANTHROPIC_API_KEY="sk-ant-..."
```

To populate MongoDB from the raw CSV once, use `push_data.py`.

## Running

### Full training pipeline

```bash
python main.py
```

On success you'll find:

```
artifacts/<timestamp>/
  data_ingestion/
    feature_store/NetworkData.csv
    ingested/train.csv, test.csv
  data_validation/
    validated/train.csv, test.csv
    data_drift_report/data_drift_report.yaml
  data_transformation/
    transformed/train.npy, test.npy
    transformed_object/preprocessor.pkl
  model_trainer/
    trained_model/model.pkl
```

`model.pkl` contains a `NetworkModel` (see
`utils/ml_utils/metric/model/estimator.py`) that wraps the preprocessor and
the fitted classifier, so downstream callers only need
`model.predict(raw_df)`.

### Serving

```bash

# Streamlit
streamlit run streamlit_app.py
```

## Configuration

Everything tunable is in
`network_security/constants/training_pipeline/__init__.py`:

| Constant | Purpose |
| --- | --- |
| `DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO` | Initial holdout fraction (default 0.2) |
| `DATA_TRANSFORMATION_IMPUTER_PARAMS` | `KNNImputer` kwargs (3 neighbors, uniform) |
| `MODEL_TRAINER_EXPECTED_SCORE` | Minimum test F1 to accept the model (0.6) |
| `MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD` | Max allowed train/test F1 gap (0.05) |
| `TARGET_COLUMN` | Label column name (`Result`) |

Hyper-parameter grids for each candidate model are defined in
`ModelTrainer._candidate_models`.

## Project layout

```
main.py                                  # pipeline entry point
push_data.py                             # one-shot CSV -> MongoDB loader
app.py                                   # FastAPI serving + explainability
streamlit_app.py                         # Streamlit UI
static/index.html                        # interactive single-page classifier UI
network_security/
  components/                            # ingestion / validation / transformation
  entity/                                # config + artifact dataclasses
  constants/training_pipeline/           # all tunable constants
  exception/, logger/                    # cross-cutting infra
  model_trainer.py                       # training + selection + gating
  explainer.py                           # SHAP + Claude explanation engine
  url_features.py                        # live URL -> 30-feature extraction
  feature_dictionary.py                  # feature names + human-readable descriptions
utils/
  main_utils/                            # yaml / numpy / pickle helpers
  ml_utils/metric/                       # classification metric + NetworkModel wrapper
data_schema/schema.yaml                  # column count / dtypes for validation
```

## Recent results

Across multiple training runs, the pipeline consistently selects either
**Random Forest** or **Gradient Boosting** as the best model, achieving:

- **Test F1**: 0.970 – 0.980
- **Test Precision**: 0.957 – 0.975
- **Test Recall**: 0.976 – 0.988
- **Train/test F1 gap**: < 0.022 (well within the 0.05 threshold)

## Known limitations

- Grids are a reasonable first pass, not exhaustive; tune
  `_candidate_models` for serious runs.
- Drift detection is column-wise KS only; no multivariate drift or
  categorical handling.
- The pipeline re-runs end-to-end; no caching between stages.
- No CLI flags — everything is driven by the constants module.
- Five reputation features require paid APIs and default to 0 during live
  URL analysis.