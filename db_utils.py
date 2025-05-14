from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'ahpmoi')

def get_db():
    """Kết nối và trả về database instance"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test kết nối
        client.server_info()
        db = client[DB_NAME]
        
        # Tạo index cho collection
        history_collection = db["ahp_history"]
        history_collection.create_index([("timestamp", -1)])
        history_collection.create_index([("name", "text")])
        
        return db
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"Lỗi kết nối MongoDB: {e}")
        raise

def save_to_history(data):
    """Lưu kết quả AHP vào lịch sử"""
    try:
        db = get_db()
        history_collection = db["ahp_history"]
        
        history_doc = {
            "name": data.get("name", "Unnamed Analysis"),
            "timestamp": datetime.now(),
            "criteria": data.get("criteria", []),
            "alternatives": data.get("alternatives", []),
            "criteria_weights": data.get("criteria_weights", []),
            "alternative_weights": data.get("alternative_weights", []),
            "final_scores": data.get("final_scores", []),
            "consistency_ratio": data.get("consistency_ratio", 0)
        }
        result = history_collection.insert_one(history_doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Lỗi khi lưu lịch sử: {e}")
        return None 