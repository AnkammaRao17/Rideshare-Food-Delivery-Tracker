"""
Database management module for MongoDB using PyMongo.
Handles connection pooling, schema initialization, index creation, and helpers.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from bson import ObjectId
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError

from config import MONGO_URI, DATABASE_NAME, COLLECTIONS
from models.schemas import VALIDATORS

logger = logging.getLogger(__name__)

# Client singleton cache
_client_instance: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Get or initialize singleton MongoClient with optimized connection pooling."""
    global _client_instance
    if _client_instance is None:
        try:
            _client_instance = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=5
            )
        except Exception as e:
            logger.error(f"Failed to instantiate MongoClient: {e}")
            raise
    return _client_instance


def get_db(db_name: Optional[str] = None):
    """
    Get MongoDB database instance.
    Defaults to configured DATABASE_NAME.
    """
    client = get_client()
    target_db_name = db_name or DATABASE_NAME
    return client[target_db_name]


def ping_db() -> Tuple[bool, Dict[str, Any]]:
    """
    Ping MongoDB to verify active connection.
    Returns (is_connected, info_dict).
    """
    try:
        client = get_client()
        server_info = client.server_info()
        return True, {
            "version": server_info.get("version"),
            "host": client.HOST,
            "port": client.PORT,
            "status": "connected"
        }
    except ConnectionFailure as ce:
        return False, {"status": "connection_failed", "error": str(ce)}
    except Exception as e:
        return False, {"status": "error", "error": str(e)}


def init_db(db_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize database collections with JSON Schema validators and required indexes.
    Idempotent and safe to run multiple times.
    """
    db = get_db(db_name)
    existing_collections = db.list_collection_names()
    results = {"created_collections": [], "updated_validators": [], "indexes_created": []}

    # 1. Apply Validators
    for col_name, validator in VALIDATORS.items():
        if col_name not in existing_collections:
            try:
                db.create_collection(
                    col_name,
                    validator=validator,
                    validationLevel="moderate",
                    validationAction="error"
                )
                results["created_collections"].append(col_name)
            except Exception as e:
                logger.warning(f"Could not create collection {col_name} with validator: {e}")
        else:
            try:
                db.command({
                    "collMod": col_name,
                    "validator": validator,
                    "validationLevel": "moderate",
                    "validationAction": "error"
                })
                results["updated_validators"].append(col_name)
            except Exception as e:
                logger.warning(f"Could not update validator on {col_name}: {e}")

    # 2. Setup Required Indexes
    try:
        # Users indexes: unique email
        db.users.create_index([("email", ASCENDING)], unique=True, name="idx_users_email_unique")
        db.users.create_index([("created_at", DESCENDING)], name="idx_users_created_at")
        results["indexes_created"].append("users: email (unique), created_at")

        # Drivers indexes: availability, rating
        db.drivers.create_index([("availability", ASCENDING)], name="idx_drivers_availability")
        db.drivers.create_index([("rating", DESCENDING)], name="idx_drivers_rating")
        results["indexes_created"].append("drivers: availability, rating")

        # Rides indexes: status, driver_id, user_id, created_at, compound
        db.rides.create_index([("status", ASCENDING)], name="idx_rides_status")
        db.rides.create_index([("created_at", DESCENDING)], name="idx_rides_created_at")
        db.rides.create_index([("driver_id", ASCENDING)], name="idx_rides_driver_id")
        db.rides.create_index([("user_id", ASCENDING)], name="idx_rides_user_id")
        db.rides.create_index(
            [("driver_id", ASCENDING), ("status", ASCENDING)],
            name="idx_rides_driver_status"
        )
        db.rides.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
            name="idx_rides_status_created_at"
        )
        db.rides.create_index([("fare", DESCENDING)], name="idx_rides_fare")
        results["indexes_created"].append("rides: status, created_at, driver_id, user_id, compound")

        # Restaurants indexes: cuisine, rating, is_active
        db.restaurants.create_index([("cuisine", ASCENDING)], name="idx_restaurants_cuisine")
        db.restaurants.create_index([("rating", DESCENDING)], name="idx_restaurants_rating")
        db.restaurants.create_index([("is_active", ASCENDING)], name="idx_restaurants_is_active")
        results["indexes_created"].append("restaurants: cuisine, rating, is_active")

        # Food orders indexes: status, restaurant_id, user_id, created_at, compound
        db.food_orders.create_index([("status", ASCENDING)], name="idx_orders_status")
        db.food_orders.create_index([("restaurant_id", ASCENDING)], name="idx_orders_restaurant_id")
        db.food_orders.create_index([("user_id", ASCENDING)], name="idx_orders_user_id")
        db.food_orders.create_index([("created_at", DESCENDING)], name="idx_orders_created_at")
        db.food_orders.create_index(
            [("restaurant_id", ASCENDING), ("status", ASCENDING)],
            name="idx_orders_restaurant_status"
        )
        db.food_orders.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
            name="idx_orders_status_created_at"
        )
        results["indexes_created"].append("food_orders: status, restaurant_id, user_id, compound")
    except Exception as e:
        logger.warning(f"Error creating indexes during init_db: {e}")

    return results


def reset_db(db_name: Optional[str] = None, confirm: bool = False) -> bool:
    """
    Safely reset the database by dropping its collections.
    Requires explicit confirm=True.
    """
    if not confirm:
        raise ValueError("Explicit confirmation (confirm=True) required to reset the database.")
    
    target_name = db_name or DATABASE_NAME
    client = get_client()
    client.drop_database(target_name)
    init_db(target_name)
    return True


def doc_to_dict(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively transform BSON document into JSON/Python-native types for UI & Pandas.
    Converts ObjectId -> str, datetime -> formatted string.
    """
    if doc is None:
        return None
    
    res = {}
    for key, val in doc.items():
        if isinstance(val, ObjectId):
            res[key] = str(val)
        elif isinstance(val, datetime):
            res[key] = val.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(val, list):
            res[key] = [
                doc_to_dict(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item.strftime("%Y-%m-%d %H:%M:%S") if isinstance(item, datetime)
                else item
                for item in val
            ]
        elif isinstance(val, dict):
            res[key] = doc_to_dict(val)
        else:
            res[key] = val
    return res
