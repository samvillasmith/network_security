import os 
import sys
import numpy as np
import pandas as pd


"""
Defining common constant variables for the training pipeline. This file will be imported in the training pipeline component of the training pipeline.
"""

TARGET_COLUMN: str = "Result"
PIPELINE_NAME: str = "network_security_training_pipeline"
ARTIFACT_DIR: str = "artifacts"
FILE_NAME: str = "NetworkData.csv"

TRAIN_FILE_NAME: str = "train.csv"
TEST_FILE_NAME: str = "test.csv"

SCHEMA_FILE_PATH: str = os.path.join("data_schema", "schema.yaml")



DATA_INGESTION_COLLECTION_NAME: str = "NetworkData"
DATA_INGESTION_DATABASE_NAME: str = "NetworkSecurity"
DATA_INGESTION_DIR_NAME: str = "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO: float = 0.2

DATA_VALIDATION_DIR_NAME: str = "data_validation"
DATA_VALIDATION_VALID_DIR_NAME: str = "validated"
DATA_VALIDATION_INVALID_DIR_NAME: str = "invalid"
DATA_VALIDATION_DRIFT_REPORT_DIR_NAME: str = "data_drift_report"
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME: str = "data_drift_report.yaml"

DATA_TRANSFORMATION_DIR_NAME: str = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR_NAME: str = "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR_NAME: str = "transformed_object"

DATA_TRANSFORMATION_IMPUTER_PARAMS: dict = {
    "missing_values": np.nan,
    "n_neighbors": 3,
    "weights": "uniform"
}

PREPROCESSOR_OBJECT_FILE_NAME: str = "preprocessor.pkl"

MODEL_TRAINER_DIR_NAME: str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_FILE_NAME: str = "model.pkl"
MODEL_TRAINER_EXPECTED_SCORE: float = 0.6
MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD: float = 0.05

SAVED_MODEL_DIR = os.path.join("saved_models")
MODEL_FILE_NAME = "model.pkl"