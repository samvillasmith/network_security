import sys

from network_security.components.data_ingestion import DataIngestion
from network_security.components.data_validation import DataValidation
from network_security.components.data_transformation import DataTransformation
from network_security.model_trainer import ModelTrainer
from network_security.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
)
from network_security.exception.exception import NetworkSecurityException
from network_security.logger.custom_logger import logger


if __name__ == "__main__":
    try:
        training_pipeline_config = TrainingPipelineConfig()

        data_ingestion_config = DataIngestionConfig(training_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config)
        logger.info("Data ingestion initiated.")
        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
        logger.info(f"Data ingestion completed: {data_ingestion_artifact}")

        data_validation_config = DataValidationConfig(training_pipeline_config)
        data_validation = DataValidation(
            data_validation_config=data_validation_config,
            data_ingestion_artifact=data_ingestion_artifact,
        )
        logger.info("Data validation initiated.")
        data_validation_artifact = data_validation.initiate_data_validation()
        logger.info(f"Data validation completed: {data_validation_artifact}")

        data_transformation_config = DataTransformationConfig(training_pipeline_config)
        data_transformation = DataTransformation(
            data_validation_artifact=data_validation_artifact,
            data_transformation_config=data_transformation_config,
        )
        logger.info("Data transformation initiated.")
        data_transformation_artifact = data_transformation.initiate_data_transformation()
        logger.info(f"Data transformation completed: {data_transformation_artifact}")

        model_trainer_config = ModelTrainerConfig(training_pipeline_config)
        model_trainer = ModelTrainer(
            model_trainer_config=model_trainer_config,
            data_transformation_artifact=data_transformation_artifact,
        )
        logger.info("Model training initiated.")
        model_trainer_artifact = model_trainer.initiate_model_trainer()
        logger.info(f"Model training completed: {model_trainer_artifact}")

    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
