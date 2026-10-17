"""
Restaurant CRUD service for MongoDB.
"""

from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId

from db import get_db, doc_to_dict
from models.validation import (
    validate_object_id,
    validate_restaurant_payload,
    ValidationError,
    NotFoundError
)


def create_restaurant(payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Create a new restaurant."""
    database = db if db is not None else get_db()
    validated = validate_restaurant_payload(payload)
    
    doc = {
        "name": validated["name"],
        "cuisine": validated["cuisine"],
        "location": validated["location"],
        "rating": validated["rating"],
        "is_active": validated["is_active"]
    }
    
    result = database.restaurants.insert_one(doc)
    if not result.inserted_id:
        raise RuntimeError("MongoDB insert failed: No inserted_id returned from database.")
    saved = database.restaurants.find_one({"_id": result.inserted_id})
    if not saved:
        raise RuntimeError(f"MongoDB read-back verification failed: Restaurant '{result.inserted_id}' not found after insertion.")
    return doc_to_dict(saved)


def get_restaurant_by_id(restaurant_id: str, db=None) -> Dict[str, Any]:
    """Retrieve single restaurant by ObjectId string."""
    database = db if db is not None else get_db()
    oid = validate_object_id(restaurant_id, "restaurant_id")
    restaurant = database.restaurants.find_one({"_id": oid})
    if not restaurant:
        raise NotFoundError(f"Restaurant with ID '{restaurant_id}' not found.")
    return doc_to_dict(restaurant)


def get_restaurants(
    search: Optional[str] = None,
    cuisine: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_rating: Optional[float] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "name",
    sort_dir: int = 1,
    db=None
) -> Tuple[List[Dict[str, Any]], int]:
    """Get paginated restaurants with filters."""
    database = db if db is not None else get_db()
    query = {}
    
    if search and search.strip():
        term = search.strip()
        query["$or"] = [
            {"name": {"$regex": term, "$options": "i"}},
            {"location": {"$regex": term, "$options": "i"}}
        ]
        
    if cuisine and cuisine != "All":
        query["cuisine"] = cuisine
        
    if is_active is not None:
        query["is_active"] = is_active
        
    if min_rating is not None and min_rating > 0:
        query["rating"] = {"$gte": min_rating}
        
    total_count = database.restaurants.count_documents(query)
    skip = max(0, (page - 1) * limit)
    
    cursor = database.restaurants.find(query).sort(sort_by, sort_dir).skip(skip).limit(limit)
    restaurants = [doc_to_dict(r) for r in cursor]
    return restaurants, total_count


def update_restaurant(restaurant_id: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Update restaurant information."""
    database = db if db is not None else get_db()
    oid = validate_object_id(restaurant_id, "restaurant_id")
    
    existing = database.restaurants.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Restaurant with ID '{restaurant_id}' not found.")
        
    validated = validate_restaurant_payload(payload)
    
    update_data = {
        "name": validated["name"],
        "cuisine": validated["cuisine"],
        "location": validated["location"],
        "rating": validated["rating"],
        "is_active": validated["is_active"]
    }
    
    database.restaurants.update_one({"_id": oid}, {"$set": update_data})
    updated = database.restaurants.find_one({"_id": oid})
    return doc_to_dict(updated)


def delete_restaurant(restaurant_id: str, db=None) -> bool:
    """Delete a restaurant if no active food orders are open."""
    database = db if db is not None else get_db()
    oid = validate_object_id(restaurant_id, "restaurant_id")
    
    existing = database.restaurants.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Restaurant with ID '{restaurant_id}' not found.")
        
    active_orders = database.food_orders.count_documents({
        "restaurant_id": oid,
        "status": {"$in": ["placed", "preparing", "out_for_delivery"]}
    })
    if active_orders > 0:
        raise ValidationError(f"Cannot delete restaurant: {active_orders} active order(s) pending.")
        
    database.restaurants.delete_one({"_id": oid})
    return True


def get_all_restaurants_dropdown(db=None) -> List[Dict[str, str]]:
    """Return lightweight list for selectbox UI."""
    database = db if db is not None else get_db()
    cursor = database.restaurants.find({}, {"name": 1, "cuisine": 1, "location": 1}).sort("name", 1)
    return [
        {
            "_id": str(r["_id"]),
            "label": f"{r.get('name', 'N/A')} ({r.get('cuisine', '')} - {r.get('location', '')})"
        }
        for r in cursor
    ]
