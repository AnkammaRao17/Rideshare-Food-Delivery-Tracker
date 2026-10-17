"""
Rides CRUD and management service.
Handles validation, joins with users and drivers, and status transitions.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId

from db import get_db, doc_to_dict
from models.validation import (
    validate_object_id,
    validate_ride_payload,
    ValidationError,
    NotFoundError
)


def create_ride(payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Create a new ride after validating foreign keys and constraints."""
    database = db if db is not None else get_db()
    validated = validate_ride_payload(payload, db=database)
    
    doc = {
        "user_id": validated["user_id"],
        "driver_id": validated["driver_id"],
        "pickup_location": validated["pickup_location"],
        "dropoff_location": validated["dropoff_location"],
        "distance_km": validated["distance_km"],
        "fare": validated["fare"],
        "status": validated["status"],
        "created_at": datetime.now(timezone.utc),
        "completed_at": validated["completed_at"]
    }
    
    result = database.rides.insert_one(doc)
    if not result.inserted_id:
        raise RuntimeError("MongoDB insert failed: No inserted_id returned from database.")
    saved = database.rides.find_one({"_id": result.inserted_id})
    if not saved:
        raise RuntimeError(f"MongoDB read-back verification failed: Ride '{result.inserted_id}' not found after insertion.")
    return doc_to_dict(saved)


def get_ride_by_id(ride_id: str, db=None) -> Dict[str, Any]:
    """Retrieve a single ride with joined user and driver details."""
    database = db if db is not None else get_db()
    oid = validate_object_id(ride_id, "ride_id")
    
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
                "from": "drivers",
                "localField": "driver_id",
                "foreignField": "_id",
                "as": "driver"
            }
        },
        {"$unwind": {"path": "$driver", "preserveNullAndEmptyArrays": True}}
    ]
    
    results = list(database.rides.aggregate(pipeline))
    if not results:
        raise NotFoundError(f"Ride with ID '{ride_id}' not found.")
    return doc_to_dict(results[0])


def get_rides(
    status: Optional[str] = None,
    driver_id: Optional[str] = None,
    user_id: Optional[str] = None,
    min_fare: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_dir: int = -1,
    db=None
) -> Tuple[List[Dict[str, Any]], int]:
    """Query paginated rides with compound filters and joins."""
    database = db if db is not None else get_db()
    match_stage = {}
    
    if status and status != "All":
        match_stage["status"] = status
        
    if driver_id and driver_id != "All":
        match_stage["driver_id"] = validate_object_id(driver_id, "driver_id")
        
    if user_id and user_id != "All":
        match_stage["user_id"] = validate_object_id(user_id, "user_id")
        
    if min_fare is not None and min_fare > 0:
        match_stage["fare"] = {"$gte": float(min_fare)}
        
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        match_stage["created_at"] = date_filter
        
    total_count = database.rides.count_documents(match_stage)
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
                "user_id": 1,
                "driver_id": 1,
                "user_name": "$user.name",
                "user_email": "$user.email",
                "driver_name": "$driver.name",
                "driver_vehicle": "$driver.vehicle_type",
                "pickup_location": 1,
                "dropoff_location": 1,
                "distance_km": 1,
                "fare": 1,
                "status": 1,
                "created_at": 1,
                "completed_at": 1
            }
        }
    ]
    
    results = list(database.rides.aggregate(pipeline))
    return [doc_to_dict(r) for r in results], total_count


def update_ride(ride_id: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Update ride details and timestamp transitions."""
    database = db if db is not None else get_db()
    oid = validate_object_id(ride_id, "ride_id")
    
    existing = database.rides.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Ride with ID '{ride_id}' not found.")
        
    validated = validate_ride_payload(payload, db=database)
    
    # Check if newly set to completed
    if validated["status"] == "completed" and existing.get("status") != "completed":
        completed_at = datetime.now(timezone.utc)
    elif validated["status"] == "completed":
        completed_at = existing.get("completed_at") or datetime.now(timezone.utc)
    else:
        completed_at = None
        
    update_data = {
        "user_id": validated["user_id"],
        "driver_id": validated["driver_id"],
        "pickup_location": validated["pickup_location"],
        "dropoff_location": validated["dropoff_location"],
        "distance_km": validated["distance_km"],
        "fare": validated["fare"],
        "status": validated["status"],
        "completed_at": completed_at
    }
    
    database.rides.update_one({"_id": oid}, {"$set": update_data})
    return get_ride_by_id(ride_id, db=database)


def delete_ride(ride_id: str, db=None) -> bool:
    """Delete a ride record."""
    database = db if db is not None else get_db()
    oid = validate_object_id(ride_id, "ride_id")
    
    existing = database.rides.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Ride with ID '{ride_id}' not found.")
        
    database.rides.delete_one({"_id": oid})
    return True
