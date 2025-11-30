from pymongo import MongoClient
import os

def get_db():
    """Connect to MongoDB and return database instance"""
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db_name = os.getenv('DB_NAME', 'workout_tracker')
    return client[db_name]
