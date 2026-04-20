from network_security.components.data_ingestion import DataIngestion
from network_security.exception.exception import NetworkSecurityException
from network_security.entity.config_entity import DataIngestionConfig, DataValidationConfig, TrainingPipelineConfig
from network_security.logger.custom_logger import logger
from network_security.components.data_validation import DataValidation

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


    except Exception as e:
        raise NetworkSecurityException(e, sys)