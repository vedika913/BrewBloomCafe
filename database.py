from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

try:
    client.admin.command("ping")
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print("❌ Error:", e)

db = client["CoffeeShop"]
users = db["users"]
coffees = db["coffees"]
orders = db["orders"]

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["CoffeeShop"]

users = db["users"]
coffees = db["coffees"]
orders = db["orders"]

# NEW
messages = db["messages"]