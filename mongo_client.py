from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
db = client["cell_expansion_war"]
game_history_collection = db["game_histories"]
