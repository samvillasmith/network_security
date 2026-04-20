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

"""
Data ingestion related constants
"""

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