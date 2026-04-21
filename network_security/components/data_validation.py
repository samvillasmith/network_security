from network_security.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from network_security.entity.config_entity import DataValidationConfig
from network_security.exception.exception import NetworkSecurityException
from network_security.logger.custom_logger import logger
from network_security.constants.training_pipeline import SCHEMA_FILE_PATH, TRAIN_FILE_NAME, TEST_FILE_NAME
from utils.main_utils import read_yaml_file, write_yaml_file

from scipy.stats import ks_2samp
import os, sys
import pandas as pd

class DataValidation:
    def __init__(      
            self, 
            data_validation_config: DataValidationConfig, 
            data_ingestion_artifact: DataIngestionArtifact
            ):
        
        try:

            self.data_validation_config = data_validation_config
            self.data_ingestion_artifact = data_ingestion_artifact
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            number_of_columns = len(self._schema_config["columns"])
            logger.info(f"Required number of columns: {number_of_columns}")
            logger.info(f"Dataframe has columns: {dataframe.columns}")
            if len(dataframe.columns) == number_of_columns:
                    return True
            else:
                return False
        except Exception as e:
            raise NetworkSecurityException(e, sys)        
        
    def detect_dataset_drift(self, base_df, current_df, threshold=0.05) -> bool:
        try:
            status = True
            report = {}
            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]
                is_sample_dist = ks_2samp(d1, d2)
                if threshold <= is_sample_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False
                report.update({column: {
                    "p_value": float(is_sample_dist.pvalue),
                    "drift_status": is_found
                }})
            drift_report_file_path = self.data_validation_config.drift_report_file_path
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path, exist_ok=True)
            write_yaml_file(file_path=drift_report_file_path, content=report)

            return status

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            train_file_path = self.data_ingestion_artifact.train_file_path 
            test_file_path = self.data_ingestion_artifact.test_file_path
            train_dataframe = DataValidation.read_data(train_file_path)
            test_dataframe = DataValidation.read_data(test_file_path)

            if not self.validate_number_of_columns(dataframe=train_dataframe):
                error_message = f"Data validation failed. Number of columns in the training data is not as per the schema. Expected: {len(self._schema_config['columns'])}, Got: {len(train_dataframe.columns)}"
                logger.error(error_message)
                raise NetworkSecurityException(error_message, sys)

            if not self.validate_number_of_columns(dataframe=test_dataframe):
                error_message = f"Data validation failed. Number of columns in the testing data is not as per the schema. Expected: {len(self._schema_config['columns'])}, Got: {len(test_dataframe.columns)}"
                logger.error(error_message)
                raise NetworkSecurityException(error_message, sys)
            
            status = self.detect_dataset_drift(base_df = train_dataframe, current_df = test_dataframe)
            os.makedirs(self.data_validation_config.valid_data_dir, exist_ok=True)

            valid_train_file_path = os.path.join(self.data_validation_config.valid_data_dir, TRAIN_FILE_NAME)
            valid_test_file_path = os.path.join(self.data_validation_config.valid_data_dir, TEST_FILE_NAME)
            train_dataframe.to_csv(valid_train_file_path, index=False, header=True)
            test_dataframe.to_csv(valid_test_file_path, index=False, header=True)

            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=valid_train_file_path,
                valid_test_file_path=valid_test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )

            return data_validation_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)
