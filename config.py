"""
Configuration module for Rideshare & Food Delivery Tracker.
Loads environment variables safely and defines constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# MongoDB Settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rideshare_delivery_db")
TEST_DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "rideshare_delivery_test_db")

# Streamlit App Settings
APP_PORT = int(os.getenv("APP_PORT", 8501))
APP_HOST = os.getenv("APP_HOST", "localhost")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Collections
COLLECTIONS = {
    "USERS": "users",
    "DRIVERS": "drivers",
    "RIDES": "rides",
    "RESTAURANTS": "restaurants",
    "FOOD_ORDERS": "food_orders",
}

# Domain Enum constants
RIDE_STATUSES = ["requested", "accepted", "in_progress", "completed", "cancelled"]
ORDER_STATUSES = ["placed", "preparing", "out_for_delivery", "delivered", "cancelled"]
VEHICLE_TYPES = ["Sedan", "SUV", "Hatchback", "Bike", "Auto", "EV Sedan"]
CUISINE_TYPES = [
    "North Indian", "South Indian", "Chinese", "Italian",
    "American", "Mexican", "Continental", "Japanese", "Bakery & Desserts"
]
