"""
User CRUD service for MongoDB.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from db import get_db, doc_to_dict
from models.validation import (
    validate_object_id,
    validate_user_payload,
    ValidationError,
    NotFoundError,
    DuplicateRecordError
)


def create_user(payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Create a new user with validation and duplicate email check."""
    database = db if db is not None else get_db()
    validated = validate_user_payload(payload)
    
    # Check for existing email in python layer as well
    if database.users.find_one({"email": validated["email"]}):
        raise DuplicateRecordError(f"A user with email '{validated['email']}' already exists.")
        
    doc = {
        "name": validated["name"],
        "email": validated["email"],
        "phone": validated["phone"],
        "created_at": datetime.now(timezone.utc)
    }
    
    try:
        result = database.users.insert_one(doc)
        if not result.inserted_id:
            raise RuntimeError("MongoDB insert failed: No inserted_id returned from database.")
        saved = database.users.find_one({"_id": result.inserted_id})
        if not saved:
            raise RuntimeError(f"MongoDB read-back verification failed: User '{result.inserted_id}' not found after insertion.")
        return doc_to_dict(saved)
    except DuplicateKeyError:
        raise DuplicateRecordError(f"Email '{validated['email']}' is already registered (unique index violation).")


def get_user_by_id(user_id: str, db=None) -> Dict[str, Any]:
    """Retrieve single user by ObjectId string."""
    database = db if db is not None else get_db()
    oid = validate_object_id(user_id, "user_id")
    user = database.users.find_one({"_id": oid})
    if not user:
        raise NotFoundError(f"User with ID '{user_id}' not found.")
    return doc_to_dict(user)


def get_users(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_dir: int = -1,
    db=None
) -> Tuple[List[Dict[str, Any]], int]:
    """Get paginated users with optional name/email/phone search."""
    database = db if db is not None else get_db()
    query = {}
    
    if search and search.strip():
        term = search.strip()
        query["$or"] = [
            {"name": {"$regex": term, "$options": "i"}},
            {"email": {"$regex": term, "$options": "i"}},
            {"phone": {"$regex": term, "$options": "i"}}
        ]
        
    total_count = database.users.count_documents(query)
    skip = max(0, (page - 1) * limit)
    
    cursor = database.users.find(query).sort(sort_by, sort_dir).skip(skip).limit(limit)
    users = [doc_to_dict(u) for u in cursor]
    return users, total_count


def update_user(user_id: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Update existing user."""
    database = db if db is not None else get_db()
    oid = validate_object_id(user_id, "user_id")
    
    existing = database.users.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"User with ID '{user_id}' not found.")
        
    validated = validate_user_payload(payload)
    
    # Check if new email clashes with another user
    clash = database.users.find_one({"email": validated["email"], "_id": {"$ne": oid}})
    if clash:
        raise DuplicateRecordError(f"Email '{validated['email']}' is already taken by another user.")
        
    update_data = {
        "name": validated["name"],
        "email": validated["email"],
        "phone": validated["phone"]
    }
    
    try:
        database.users.update_one({"_id": oid}, {"$set": update_data})
        updated = database.users.find_one({"_id": oid})
        return doc_to_dict(updated)
    except DuplicateKeyError:
        raise DuplicateRecordError(f"Email '{validated['email']}' already exists.")


def delete_user(user_id: str, db=None) -> bool:
    """Delete a user if they have no active/in-progress rides or orders."""
    database = db if db is not None else get_db()
    oid = validate_object_id(user_id, "user_id")
    
    existing = database.users.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"User with ID '{user_id}' not found.")
        
    # Check active rides
    active_rides = database.rides.count_documents({
        "user_id": oid,
        "status": {"$in": ["requested", "accepted", "in_progress"]}
    })
    if active_rides > 0:
        raise ValidationError(f"Cannot delete user: {active_rides} active ride(s) exist for this user.")
        
    # Check active food orders
    active_orders = database.food_orders.count_documents({
        "user_id": oid,
        "status": {"$in": ["placed", "preparing", "out_for_delivery"]}
    })
    if active_orders > 0:
        raise ValidationError(f"Cannot delete user: {active_orders} active food order(s) exist for this user.")
        
    database.users.delete_one({"_id": oid})
    return True


def get_all_users_dropdown(db=None) -> List[Dict[str, str]]:
    """Return lightweight list for selectbox UI dropdowns."""
    database = db if db is not None else get_db()
    cursor = database.users.find({}, {"name": 1, "email": 1}).sort("name", 1)
    return [{"_id": str(u["_id"]), "label": f"{u.get('name', 'N/A')} ({u.get('email', '')})"} for u in cursor]
