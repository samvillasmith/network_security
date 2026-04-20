from network_security.components.data_ingestion import DataIngestion
from network_security.exception.exception import NetworkSecurityException
from network_security.entity.config_entity import DataIngestionConfig, DataValidationConfig, TrainingPipelineConfig
from network_security.logger.custom_logger import logger
from network_security.components.data_validation import DataValidation
from network_security.components.data_transformation import DataTransformation, DataTransformationArtifact, DataValidationArtifact, DataTransformationConfig

import sys

if __name__ == "__main__":
    try:

        training_pipeline_config = TrainingPipelineConfig()
        data_ingestion_config = DataIngestionConfig(training_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config)
        data_ingestion.initiate_data_ingestion()
        logger.info("Data ingestion initiated.")
        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
        logger.info(f"Data initiation completed and artifact: {data_ingestion_artifact} created.")
        data_validation_config = DataValidationConfig(training_pipeline_config)
        data_validation = DataValidation(data_validation_config=data_validation_config, data_ingestion_artifact=data_ingestion_artifact)
        logger.info("Data validation initiated.")
        data_validation_artifact = data_validation.initiate_data_validation()
        logger.info(f"Data validation completed and artifact: {data_validation_artifact} created.")
        logger.info("Data transformation initiated.")
        data_transformation_config = DataTransformationConfig(training_pipeline_config)
        data_transformation = DataTransformation(data_validation_artifact=data_validation_artifact, data_transformation_config=data_transformation_config)
        data_transformation_artifact = data_transformation.initiate_data_transformation()
        logger.info(f"Data transformation completed and artifact: {data_transformation_artifact} created.")



    except Exception as e:
        raise NetworkSecurityException(e, sys)