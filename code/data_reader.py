import os
import pandas as pd

class DataReader:
    @staticmethod
    def read(file_path):
        name, file_type = os.path.splitext(file_path)
        file_type = file_type.lower()

        if file_type == ".json":
            df = pd.read_json(file_path)
        elif file_type == ".csv":
            df = pd.read_csv(file_path)
        elif file_type == ".xml":
            df = pd.read_xml(file_path)

        return df