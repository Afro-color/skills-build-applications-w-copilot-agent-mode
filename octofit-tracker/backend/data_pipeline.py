from pymongo import MongoClient
from transformers import pipeline
import torch

class DataPipeline:
    def __init__(self, mongo_uri, db_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.model_pipeline = pipeline('text-classification', model='distilbert-base-uncased', device=0 if torch.cuda.is_available() else -1)

    def fetch_data(self, collection_name):
        """Fetch data from MongoDB."""
        collection = self.db[collection_name]
        return list(collection.find())

    def process_data(self, data):
        """Process data using the transformers pipeline."""
        return [self.model_pipeline(item['text']) for item in data]

    def save_results(self, collection_name, results):
        """Save processed results back to MongoDB."""
        collection = self.db[collection_name]
        collection.insert_many(results)
