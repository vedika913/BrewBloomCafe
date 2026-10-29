
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully!")
except Exception as e:
    print("MongoDB Error:", e)

db = client["CoffeeShop"]

users = db["users"]
coffees = db["coffees"]
orders = db["orders"]
messages = db["messages"]
