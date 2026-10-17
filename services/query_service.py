"""
Advanced MongoDB query demonstrations.
Demonstrates operators like $gt, $gte, $lt, $in, $and, $or, compound queries, and projections.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId

from db import get_db, doc_to_dict
from models.validation import validate_object_id


def query_rides_above_fare(min_fare: float, status: Optional[str] = None, limit: int = 50, db=None) -> List[Dict[str, Any]]:
    """
    Demonstrates $gt / $gte filter on numeric field with projection.
    PyMongo: db.rides.find({"fare": {"$gt": min_fare}})
    """
    database = db if db is not None else get_db()
    query = {"fare": {"$gt": float(min_fare)}}
    if status and status != "All":
        query["status"] = status
        
    pipeline = [
        {"$match": query},
        {"$sort": {"fare": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "drivers",
                "localField": "driver_id",
                "foreignField": "_id",
                "as": "driver"
            }
        },
        {"$unwind": {"path": "$driver", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "pickup_location": 1,
                "dropoff_location": 1,
                "distance_km": 1,
                "fare": 1,
                "status": 1,
                "created_at": 1,
                "user_name": "$user.name",
                "driver_name": "$driver.name"
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.rides.aggregate(pipeline)]


def query_completed_rides_for_driver(driver_id: str, limit: int = 50, db=None) -> List[Dict[str, Any]]:
    """
    Demonstrates compound filter with ObjectId and status equality.
    PyMongo: db.rides.find({"driver_id": ObjectId(driver_id), "status": "completed"})
    """
    database = db if db is not None else get_db()
    oid = validate_object_id(driver_id, "driver_id")
    
    query = {
        "driver_id": oid,
        "status": "completed"
    }
    
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "pickup_location": 1,
                "dropoff_location": 1,
                "distance_km": 1,
                "fare": 1,
                "status": 1,
                "created_at": 1,
                "completed_at": 1,
                "user_name": "$user.name"
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.rides.aggregate(pipeline)]


def query_orders_in_date_range(
    start_date: datetime,
    end_date: datetime,
    status: Optional[str] = None,
    limit: int = 50,
    db=None
) -> List[Dict[str, Any]]:
    """
    Demonstrates range query using $gte and $lte on ISODate fields.
    PyMongo: db.food_orders.find({"created_at": {"$gte": start_date, "$lte": end_date}})
    """
    database = db if db is not None else get_db()
    query: Dict[str, Any] = {
        "created_at": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    if status and status != "All":
        query["status"] = status
        
    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "restaurant_id",
                "foreignField": "_id",
                "as": "restaurant"
            }
        },
        {"$unwind": {"path": "$restaurant", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "user_name": "$user.name",
                "restaurant_name": "$restaurant.name",
                "cuisine": "$restaurant.cuisine",
                "total_amount": 1,
                "delivery_fee": 1,
                "status": 1,
                "item_count": {"$size": "$items"},
                "created_at": 1
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.food_orders.aggregate(pipeline)]


def query_cancelled_transactions(limit: int = 50, db=None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Demonstrates $in and $or filtering for cancelled rides and orders.
    PyMongo: db.rides.find({"status": "cancelled"}) and db.food_orders.find({"status": "cancelled"})
    """
    database = db if db is not None else get_db()
    
    rides = list(database.rides.find({"status": "cancelled"}).sort("created_at", -1).limit(limit))
    orders = list(database.food_orders.find({"status": "cancelled"}).sort("created_at", -1).limit(limit))
    
    return {
        "cancelled_rides": [doc_to_dict(r) for r in rides],
        "cancelled_orders": [doc_to_dict(o) for o in orders]
    }


def query_restaurants_above_rating(
    min_rating: float,
    cuisine: Optional[str] = None,
    is_active: bool = True,
    limit: int = 50,
    db=None
) -> List[Dict[str, Any]]:
    """
    Demonstrates compound query with $gte, $eq and projection.
    PyMongo: db.restaurants.find({"rating": {"$gte": min_rating}, "is_active": True})
    """
    database = db if db is not None else get_db()
    query: Dict[str, Any] = {
        "rating": {"$gte": float(min_rating)},
        "is_active": is_active
    }
    if cuisine and cuisine != "All":
        query["cuisine"] = cuisine
        
    cursor = database.restaurants.find(query).sort("rating", -1).limit(limit)
    return [doc_to_dict(r) for r in cursor]


def query_top_customers_by_order_count(limit: int = 10, db=None) -> List[Dict[str, Any]]:
    """
    Demonstrates $group, $sort, $limit, and $lookup to aggregate customer activity.
    """
    database = db if db is not None else get_db()
    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "order_count": {"$sum": 1},
                "total_spent": {"$sum": "$total_amount"}
            }
        },
        {"$sort": {"order_count": -1, "total_spent": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 1,
                "name": "$user.name",
                "email": "$user.email",
                "phone": "$user.phone",
                "order_count": 1,
                "total_spent": {"$round": ["$total_spent", 2]}
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.food_orders.aggregate(pipeline)]


def query_top_drivers_by_completed_rides(limit: int = 10, db=None) -> List[Dict[str, Any]]:
    """
    Demonstrates aggregation with $match for status='completed', group by driver, and join.
    """
    database = db if db is not None else get_db()
    pipeline = [
        {"$match": {"status": "completed"}},
        {
            "$group": {
                "_id": "$driver_id",
                "completed_rides": {"$sum": 1},
                "total_fare_earned": {"$sum": "$fare"},
                "total_distance": {"$sum": "$distance_km"}
            }
        },
        {"$sort": {"completed_rides": -1, "total_fare_earned": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "drivers",
                "localField": "_id",
                "foreignField": "_id",
                "as": "driver"
            }
        },
        {"$unwind": "$driver"},
        {
            "$project": {
                "_id": 1,
                "driver_name": "$driver.name",
                "vehicle_type": "$driver.vehicle_type",
                "rating": "$driver.rating",
                "completed_rides": 1,
                "total_fare_earned": {"$round": ["$total_fare_earned", 2]},
                "total_distance": {"$round": ["$total_distance", 2]}
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.rides.aggregate(pipeline)]


def query_top_restaurants_by_revenue(limit: int = 10, db=None) -> List[Dict[str, Any]]:
    """
    Demonstrates aggregation on delivered food orders joined with restaurants.
    """
    database = db if db is not None else get_db()
    pipeline = [
        {"$match": {"status": "delivered"}},
        {
            "$group": {
                "_id": "$restaurant_id",
                "delivered_orders": {"$sum": 1},
                "gross_revenue": {"$sum": "$total_amount"}
            }
        },
        {"$sort": {"gross_revenue": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "_id",
                "foreignField": "_id",
                "as": "restaurant"
            }
        },
        {"$unwind": "$restaurant"},
        {
            "$project": {
                "_id": 1,
                "restaurant_name": "$restaurant.name",
                "cuisine": "$restaurant.cuisine",
                "rating": "$restaurant.rating",
                "location": "$restaurant.location",
                "delivered_orders": 1,
                "gross_revenue": {"$round": ["$gross_revenue", 2]}
            }
        }
    ]
    return [doc_to_dict(doc) for doc in database.food_orders.aggregate(pipeline)]
