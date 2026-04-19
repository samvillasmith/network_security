import os
import sys
import json
from mlflow import data
import pandas as pd
import numpy as np
import pymongo

from network_security.exception.exception import NetworkSecurityException
from network_security.logger.custom_logger import logger

from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

import certifi
ce = certifi.where()

class NetworkDataExtractor():

    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def cv_to_json_converter(self, file_path):
        try:
            data = pd.read_csv(file_path)
            records = data.to_dict(orient='records')
            return records

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def push_data_to_mongodb(self, records, database, collection):
        try:
            self.records = records
            self.mongo_client = pymongo.MongoClient(MONGODB_URL, tlsCAFile=ce)
            self.database = self.mongo_client[database]
            self.collection = self.database[collection]
            self.collection.insert_many(self.records)

            return f"{len(self.records)} records were successfully inserted into the database"

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
if __name__ == "__main__":
    FILE_PATH = "network_data/phisingData.csv"
    DATABASE = "NetworkSecurity"
    COLLECTION = "NetworkData"
    networkobject = NetworkDataExtractor()
    records = networkobject.cv_to_json_converter(file_path=FILE_PATH)
    print(records)
    number_of_records = networkobject.push_data_to_mongodb(records, DATABASE, COLLECTION)
    print(number_of_records)