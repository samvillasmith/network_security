import os
import sys

import mlflow
import mlflow.sklearn
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.tree import DecisionTreeClassifier

from network_security.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
)
from network_security.entity.config_entity import ModelTrainerConfig
from network_security.exception.exception import NetworkSecurityException
from network_security.logger.custom_logger import logger

from utils.main_utils import load_numpy_array_data, load_object, save_object
from utils.ml_utils.metric.classification_metric import get_classification_score
from utils.ml_utils.metric.model.estimator import NetworkModel


MLFLOW_EXPERIMENT = "NetworkSecurity"
VALIDATION_SIZE = 0.2
RANDOM_STATE = 42


class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact,
    ):
        self.model_trainer_config = model_trainer_config
        self.data_transformation_artifact = data_transformation_artifact

    def _candidate_models(self):
        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000),
            "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
            "AdaBoost Classifier": AdaBoostClassifier(random_state=RANDOM_STATE),
            "Gradient Boosting Classifier": GradientBoostingClassifier(random_state=RANDOM_STATE),
            "Random Forest Classifier": RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1),
        }
        params = {
            "Logistic Regression": {
                "C": [0.01, 0.1, 1.0, 10.0],
                "class_weight": [None, "balanced"],
            },
            "Decision Tree": {
                "criterion": ["gini", "entropy", "log_loss"],
                "max_depth": [None, 8, 16, 32],
                "min_samples_leaf": [1, 5, 10],
            },
            "AdaBoost Classifier": {
                "learning_rate": [0.01, 0.05, 0.1, 1.0],
                "n_estimators": [50, 100, 200],
            },
            "Gradient Boosting Classifier": {
                "learning_rate": [0.01, 0.05, 0.1],
                "n_estimators": [100, 200],
                "subsample": [0.6, 0.8, 1.0],
                "max_depth": [3, 5],
            },
            "Random Forest Classifier": {
                "n_estimators": [100, 200, 400],
                "max_depth": [None, 16, 32],
                "min_samples_leaf": [1, 2, 5],
                "class_weight": [None, "balanced"],
            },
        }
        return models, params

    def evaluate_models(self, x_train, y_train, x_val, y_val, models, params):
        fitted_models = {}
        report = {}

        for name, model in models.items():
            grid = params[name]
            logger.info(f"Fitting {name} with grid {grid}")

            if grid:
                gs = GridSearchCV(model, grid, cv=3, scoring="f1", n_jobs=-1)
                gs.fit(x_train, y_train)
                best_params = gs.best_params_
                fitted = gs.best_estimator_
            else:
                model.fit(x_train, y_train)
                best_params = {}
                fitted = model

            train_f1 = f1_score(y_train, fitted.predict(x_train))
            val_f1 = f1_score(y_val, fitted.predict(x_val))

            logger.info(f"{name}: train_f1={train_f1:.4f}, val_f1={val_f1:.4f}, params={best_params}")

            with mlflow.start_run(run_name=name, nested=True):
                mlflow.log_params({f"model": name, **{f"param_{k}": v for k, v in best_params.items()}})
                mlflow.log_metric("train_f1", train_f1)
                mlflow.log_metric("val_f1", val_f1)

            fitted_models[name] = fitted
            report[name] = val_f1

        return fitted_models, report

    def train_model(self, x_train, y_train, x_val, y_val, x_test, y_test) -> ModelTrainerArtifact:
        models, params = self._candidate_models()

        mlflow.set_experiment(MLFLOW_EXPERIMENT)
        with mlflow.start_run(run_name="model_selection"):
            fitted_models, model_report = self.evaluate_models(
                x_train, y_train, x_val, y_val, models, params,
            )

            best_model_name = max(model_report, key=model_report.get)
            best_model = fitted_models[best_model_name]
            best_val_f1 = model_report[best_model_name]

            logger.info(f"Best model on validation: {best_model_name} (val_f1={best_val_f1:.4f})")

            train_metric = get_classification_score(y_train, best_model.predict(x_train))
            test_metric = get_classification_score(y_test, best_model.predict(x_test))

            mlflow.log_param("best_model", best_model_name)
            mlflow.log_metric("best_val_f1", best_val_f1)
            mlflow.log_metric("train_f1", train_metric.f1_score)
            mlflow.log_metric("train_precision", train_metric.precision_score)
            mlflow.log_metric("train_recall", train_metric.recall_score)
            mlflow.log_metric("test_f1", test_metric.f1_score)
            mlflow.log_metric("test_precision", test_metric.precision_score)
            mlflow.log_metric("test_recall", test_metric.recall_score)

            self._enforce_quality_gates(train_metric.f1_score, test_metric.f1_score)

            preprocessor = load_object(
                file_path=self.data_transformation_artifact.transformed_object_file_path,
            )
            network_model = NetworkModel(preprocessor=preprocessor, model=best_model)

            os.makedirs(os.path.dirname(self.model_trainer_config.trained_model_file_path), exist_ok=True)
            save_object(
                file_path=self.model_trainer_config.trained_model_file_path,
                obj=network_model,
            )
            mlflow.sklearn.log_model(best_model, artifact_path="best_model")

            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                train_metric_artifact=train_metric,
                test_metric_artifact=test_metric,
            )
            logger.info(f"Model trainer artifact: {model_trainer_artifact}")
            return model_trainer_artifact

    def _enforce_quality_gates(self, train_f1: float, test_f1: float) -> None:
        expected = self.model_trainer_config.expected_accuracy
        if test_f1 < expected:
            raise NetworkSecurityException(
                Exception(
                    f"Best model test F1 ({test_f1:.4f}) is below expected threshold ({expected:.4f}). "
                    "Aborting to avoid shipping an under-performing model."
                ),
                sys,
            )

        threshold = self.model_trainer_config.overfitting_underfitting_threshold
        gap = abs(train_f1 - test_f1)
        if gap > threshold:
            raise NetworkSecurityException(
                Exception(
                    f"Train/test F1 gap ({gap:.4f}) exceeds threshold ({threshold:.4f}) — "
                    f"train_f1={train_f1:.4f}, test_f1={test_f1:.4f}. "
                    "Likely over- or under-fitting."
                ),
                sys,
            )

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_arr = load_numpy_array_data(self.data_transformation_artifact.transformed_train_file_path)
            test_arr = load_numpy_array_data(self.data_transformation_artifact.transformed_test_file_path)

            x_full, y_full = train_arr[:, :-1], train_arr[:, -1]
            x_test, y_test = test_arr[:, :-1], test_arr[:, -1]

            x_train, x_val, y_train, y_val = train_test_split(
                x_full, y_full,
                test_size=VALIDATION_SIZE,
                random_state=RANDOM_STATE,
                stratify=y_full,
            )

            return self.train_model(x_train, y_train, x_val, y_val, x_test, y_test)

        except Exception as e:
            raise NetworkSecurityException(e, sys) from e
