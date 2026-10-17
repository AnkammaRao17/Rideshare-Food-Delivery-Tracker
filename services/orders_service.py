"""
Food Orders CRUD and management service.
Handles items validation, price calculations, and joins with users and restaurants.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId

from db import get_db, doc_to_dict
from models.validation import (
    validate_object_id,
    validate_food_order_payload,
    ValidationError,
    NotFoundError
)


def create_order(payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Create a new food order after validating constraints and references."""
    database = db if db is not None else get_db()
    validated = validate_food_order_payload(payload, db=database)
    
    doc = {
        "user_id": validated["user_id"],
        "restaurant_id": validated["restaurant_id"],
        "items": validated["items"],
        "total_amount": validated["total_amount"],
        "delivery_fee": validated["delivery_fee"],
        "status": validated["status"],
        "created_at": datetime.now(timezone.utc),
        "delivered_at": validated["delivered_at"]
    }
    
    result = database.food_orders.insert_one(doc)
    if not result.inserted_id:
        raise RuntimeError("MongoDB insert failed: No inserted_id returned from database.")
    saved = database.food_orders.find_one({"_id": result.inserted_id})
    if not saved:
        raise RuntimeError(f"MongoDB read-back verification failed: Food order '{result.inserted_id}' not found after insertion.")
    return doc_to_dict(saved)


def get_order_by_id(order_id: str, db=None) -> Dict[str, Any]:
    """Retrieve single food order with joined user and restaurant details."""
    database = db if db is not None else get_db()
    oid = validate_object_id(order_id, "order_id")
    
    pipeline = [
        {"$match": {"_id": oid}},
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
                "from": "restaurants",
                "localField": "restaurant_id",
                "foreignField": "_id",
                "as": "restaurant"
            }
        },
        {"$unwind": {"path": "$restaurant", "preserveNullAndEmptyArrays": True}}
    ]
    
    results = list(database.food_orders.aggregate(pipeline))
    if not results:
        raise NotFoundError(f"Food order with ID '{order_id}' not found.")
    return doc_to_dict(results[0])


def get_orders(
    status: Optional[str] = None,
    restaurant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    min_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_dir: int = -1,
    db=None
) -> Tuple[List[Dict[str, Any]], int]:
    """Query paginated food orders with compound filters and joins."""
    database = db if db is not None else get_db()
    match_stage = {}
    
    if status and status != "All":
        match_stage["status"] = status
        
    if restaurant_id and restaurant_id != "All":
        match_stage["restaurant_id"] = validate_object_id(restaurant_id, "restaurant_id")
        
    if user_id and user_id != "All":
        match_stage["user_id"] = validate_object_id(user_id, "user_id")
        
    if min_amount is not None and min_amount > 0:
        match_stage["total_amount"] = {"$gte": float(min_amount)}
        
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        match_stage["created_at"] = date_filter
        
    total_count = database.food_orders.count_documents(match_stage)
    skip = max(0, (page - 1) * limit)
    
    pipeline = [
        {"$match": match_stage},
        {"$sort": {sort_by: sort_dir}},
        {"$skip": skip},
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
                "from": "restaurants",
                "localField": "restaurant_id",
                "foreignField": "_id",
                "as": "restaurant"
            }
        },
        {"$unwind": {"path": "$restaurant", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "user_id": 1,
                "restaurant_id": 1,
                "user_name": "$user.name",
                "restaurant_name": "$restaurant.name",
                "cuisine": "$restaurant.cuisine",
                "items": 1,
                "item_count": {"$size": {"$ifNull": ["$items", []]}},
                "total_amount": 1,
                "delivery_fee": 1,
                "status": 1,
                "created_at": 1,
                "delivered_at": 1
            }
        }
    ]
    
    results = list(database.food_orders.aggregate(pipeline))
    return [doc_to_dict(o) for r in results for o in [r]], total_count


def update_order(order_id: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Update food order details and status transitions."""
    database = db if db is not None else get_db()
    oid = validate_object_id(order_id, "order_id")
    
    existing = database.food_orders.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Food order with ID '{order_id}' not found.")
        
    validated = validate_food_order_payload(payload, db=database)
    
    if validated["status"] == "delivered" and existing.get("status") != "delivered":
        delivered_at = datetime.now(timezone.utc)
    elif validated["status"] == "delivered":
        delivered_at = existing.get("delivered_at") or datetime.now(timezone.utc)
    else:
        delivered_at = None
        
    update_data = {
        "user_id": validated["user_id"],
        "restaurant_id": validated["restaurant_id"],
        "items": validated["items"],
        "total_amount": validated["total_amount"],
        "delivery_fee": validated["delivery_fee"],
        "status": validated["status"],
        "delivered_at": delivered_at
    }
    
    database.food_orders.update_one({"_id": oid}, {"$set": update_data})
    return get_order_by_id(order_id, db=database)


def delete_order(order_id: str, db=None) -> bool:
    """Delete a food order."""
    database = db if db is not None else get_db()
    oid = validate_object_id(order_id, "order_id")
    
    existing = database.food_orders.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Food order with ID '{order_id}' not found.")
        
    database.food_orders.delete_one({"_id": oid})
    return True
