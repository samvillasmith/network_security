import yaml
from network_security.logger.custom_logger import logger
from network_security.exception.exception import NetworkSecurityException
import os, sys
import numpy as np
import pandas as pd
import dill
import pickle

def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, "rb") as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
    
def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as yaml_file:
            yaml.dump(content, yaml_file)  
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
    
def save_numpy_array_data(file_path: str, array: np.array) -> None:
    try:
        logger.info(f"Saving numpy array data to file: {file_path}")
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            np.save(file_obj, array)
        logger.info(f"Numpy array data saved successfully to file: {file_path}")
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
    
def save_object(file_path: str, obj: object) -> None:
    try:
        logger.info(f"Saving object to file: {file_path}")
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            dill.dump(obj, file_obj)
        logger.info(f"Object saved successfully to file: {file_path}")
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e

def load_object(file_path: str) -> object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exist")
        with open(file_path, "rb") as file_obj:
            return dill.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
    
def load_numpy_array_data(file_path: str) -> np.array:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exist")
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e