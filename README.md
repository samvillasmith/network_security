# Network Security — Phishing URL Classifier

End-to-end ML pipeline that trains a binary classifier on network/phishing-URL
features pulled from MongoDB and produces a serialized, ready-to-serve model.

## Pipeline stages

```
MongoDB -> DataIngestion -> DataValidation -> DataTransformation -> ModelTrainer -> saved model.pkl
```

1. **Data ingestion** (`network_security/components/data_ingestion.py`)
   Pulls the `NetworkData` collection from MongoDB, writes it to a feature
   store CSV, and produces a train/test split on disk.

2. **Data validation** (`network_security/components/data_validation.py`)
   Checks column count against `data_schema/schema.yaml` and runs a
   Kolmogorov-Smirnov drift test between train and test distributions. Writes
   a drift report to YAML.

3. **Data transformation** (`network_security/components/data_transformation.py`)
   Imputes missing values with a `KNNImputer` (params in
   `constants/training_pipeline/__init__.py`), remaps the `Result` label from
   `{-1, 1}` to `{0, 1}`, and saves transformed train/test numpy arrays plus
   the fitted preprocessor.

4. **Model trainer** (`network_security/model_trainer.py`)
   See the section below.

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
stratified). For each candidate, `GridSearchCV` (3-fold, scoring=`f1`) sweeps
a hyper-parameter grid on the training fold. The candidate with the highest
**validation** F1 is selected. Final metrics reported on the artifact are
computed on the untouched **test** set — so the headline number is not the
number the model was selected on.

### Quality gates

Before saving, two gates must pass or the pipeline raises:

- `test_f1 >= MODEL_TRAINER_EXPECTED_SCORE` (default `0.6`)
- `|train_f1 - test_f1| <= MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD`
  (default `0.05`)

Both thresholds live in `network_security/constants/training_pipeline/__init__.py`.

### Experiment tracking

Every candidate run and the final selection are logged to MLflow. By default
this writes to a local `./mlruns/` directory (experiment name
`NetworkSecurity`). To inspect results:

```bash
mlflow ui
```

Set `MLFLOW_TRACKING_URI` in your environment to point at a remote server.

## Setup

Requires Python 3.10+ and a MongoDB instance populated with the
`NetworkSecurity.NetworkData` collection.

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows bash (Git Bash / MSYS)
# or: .venv\Scripts\activate        # Windows PowerShell / cmd
pip install -r requirements.txt
```

Create a `.env` file at the project root with your Mongo connection string:

```
MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
```

To populate MongoDB from the raw CSV once, use `push_data.py`.

## Running

```bash
python main.py
```

This executes the full pipeline end-to-end. On success you'll find:

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
    trained_model/model.pkl         <-- NetworkModel (preprocessor + classifier)
logs/
  <timestamp>.log
mlruns/
  <experiment runs>
```

`model.pkl` contains a `NetworkModel` (see `utils/ml_utils/metric/model/estimator.py`)
that wraps the preprocessor and the fitted classifier, so downstream callers
only need `model.predict(raw_df)`.

## Configuration

Everything tunable is in `network_security/constants/training_pipeline/__init__.py`:

| Constant | Purpose |
| --- | --- |
| `DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO` | Initial holdout fraction (default 0.2) |
| `DATA_TRANSFORMATION_IMPUTER_PARAMS` | `KNNImputer` kwargs |
| `MODEL_TRAINER_EXPECTED_SCORE` | Minimum test F1 to accept the model |
| `MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD` | Max allowed train/test F1 gap |
| `TARGET_COLUMN` | Label column name (`Result`) |

Hyper-parameter grids for each candidate model are defined in
`ModelTrainer._candidate_models`.

## Project layout

```
main.py                                  # pipeline entry point
push_data.py                             # one-shot CSV -> MongoDB loader
network_security/
  components/                            # ingestion / validation / transformation
  entity/                                # config + artifact dataclasses
  constants/training_pipeline/           # all tunable constants
  exception/, logger/                    # cross-cutting infra
  model_trainer.py                       # training + selection + gating
utils/
  main_utils/                            # yaml / numpy / pickle helpers
  ml_utils/metric/                       # classification metric + NetworkModel wrapper
data_schema/schema.yaml                  # column count / dtypes for validation
```

## Known limitations

- Grids are a reasonable first pass, not exhaustive; tune
  `_candidate_models` for serious runs.
- Drift detection is column-wise KS only; no multivariate drift or
  categorical handling.
- The pipeline is re-run end-to-end; no caching between stages.
- No CLI flags — everything is driven by the constants module.
