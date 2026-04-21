import sys
import os
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline

from network_security.constants.training_pipeline import DATA_TRANSFORMATION_IMPUTER_PARAMS
from network_security.constants.training_pipeline import TARGET_COLUMN

from network_security.entity.artifact_entity import (
    DataValidationArtifact,
    DataTransformationArtifact
)

from network_security.entity.config_entity import DataTransformationConfig
from network_security.exception.exception import NetworkSecurityException
from network_security.logger.custom_logger import logger
from utils.main_utils import save_numpy_array_data, save_object

class DataTransformation:
    def __init__(self, data_validation_artifact: DataValidationArtifact, data_transformation_config: DataTransformationConfig):
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
        except Exception as e:  
            raise NetworkSecurityException(e, sys) from e
        
    @staticmethod
    def read_data(filepath) -> pd.DataFrame:
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    def get_data_transformer_object(cls) -> Pipeline:
        """
        This function returns a data transformer object which is a pipeline consisting of KNN imputer for handling missing values.
        """
        logger.info("Data transformation initiated.")
        try:
            imputer = KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)
            logger.info("Data transformation object created successfully.")
            processor = Pipeline(steps=[
                ("imputer", imputer)
            ])
            return processor
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e


    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logger.info("Data transformation initiated.")
            train_df = DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df = DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)

            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_train_df = train_df[TARGET_COLUMN].replace(-1, 0)

            input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_test_df = test_df[TARGET_COLUMN].replace(-1, 0)

            preprocessor = self.get_data_transformer_object()
            preprocessor_object = preprocessor.fit(input_feature_train_df)

            transformed_input_train_feature = preprocessor_object.transform(input_feature_train_df)
            transformed_input_test_feature = preprocessor_object.transform(input_feature_test_df)

            train_arr = np.c_[transformed_input_train_feature, np.array(target_feature_train_df.values)]
            test_arr = np.c_[transformed_input_test_feature, np.array(target_feature_test_df.values)]
            
            save_numpy_array_data(file_path=self.data_transformation_config.transformed_train_file_path, array=train_arr)
            save_numpy_array_data(file_path=self.data_transformation_config.transformed_test_file_path, array=test_arr)
            save_object(file_path=self.data_transformation_config.transformed_object_file_path, obj=preprocessor_object)

            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )
            return data_transformation_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys) from e
        
    