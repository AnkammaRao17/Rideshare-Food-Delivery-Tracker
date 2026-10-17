"""
Driver CRUD service for MongoDB.
"""

from typing import Optional, Dict, Any, Tuple, List
from bson import ObjectId

from db import get_db, doc_to_dict
from models.validation import (
    validate_object_id,
    validate_driver_payload,
    ValidationError,
    NotFoundError
)


def create_driver(payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Create a new driver."""
    database = db if db is not None else get_db()
    validated = validate_driver_payload(payload)
    
    doc = {
        "name": validated["name"],
        "phone": validated["phone"],
        "vehicle_type": validated["vehicle_type"],
        "vehicle_number": validated["vehicle_number"],
        "rating": validated["rating"],
        "availability": validated["availability"]
    }
    
    result = database.drivers.insert_one(doc)
    if not result.inserted_id:
        raise RuntimeError("MongoDB insert failed: No inserted_id returned from database.")
    saved = database.drivers.find_one({"_id": result.inserted_id})
    if not saved:
        raise RuntimeError(f"MongoDB read-back verification failed: Driver '{result.inserted_id}' not found after insertion.")
    return doc_to_dict(saved)


def get_driver_by_id(driver_id: str, db=None) -> Dict[str, Any]:
    """Retrieve single driver by ObjectId string."""
    database = db if db is not None else get_db()
    oid = validate_object_id(driver_id, "driver_id")
    driver = database.drivers.find_one({"_id": oid})
    if not driver:
        raise NotFoundError(f"Driver with ID '{driver_id}' not found.")
    return doc_to_dict(driver)


def get_drivers(
    search: Optional[str] = None,
    availability: Optional[bool] = None,
    vehicle_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "name",
    sort_dir: int = 1,
    db=None
) -> Tuple[List[Dict[str, Any]], int]:
    """Get paginated drivers with filters."""
    database = db if db is not None else get_db()
    query = {}
    
    if search and search.strip():
        term = search.strip()
        query["$or"] = [
            {"name": {"$regex": term, "$options": "i"}},
            {"phone": {"$regex": term, "$options": "i"}},
            {"vehicle_number": {"$regex": term, "$options": "i"}}
        ]
        
    if availability is not None:
        query["availability"] = availability
        
    if vehicle_type and vehicle_type != "All":
        query["vehicle_type"] = vehicle_type
        
    if min_rating is not None and min_rating > 0:
        query["rating"] = {"$gte": min_rating}
        
    total_count = database.drivers.count_documents(query)
    skip = max(0, (page - 1) * limit)
    
    cursor = database.drivers.find(query).sort(sort_by, sort_dir).skip(skip).limit(limit)
    drivers = [doc_to_dict(d) for d in cursor]
    return drivers, total_count


def update_driver(driver_id: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Update driver details."""
    database = db if db is not None else get_db()
    oid = validate_object_id(driver_id, "driver_id")
    
    existing = database.drivers.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Driver with ID '{driver_id}' not found.")
        
    validated = validate_driver_payload(payload)
    
    update_data = {
        "name": validated["name"],
        "phone": validated["phone"],
        "vehicle_type": validated["vehicle_type"],
        "vehicle_number": validated["vehicle_number"],
        "rating": validated["rating"],
        "availability": validated["availability"]
    }
    
    database.drivers.update_one({"_id": oid}, {"$set": update_data})
    updated = database.drivers.find_one({"_id": oid})
    return doc_to_dict(updated)


def delete_driver(driver_id: str, db=None) -> bool:
    """Delete a driver if no active rides are assigned."""
    database = db if db is not None else get_db()
    oid = validate_object_id(driver_id, "driver_id")
    
    existing = database.drivers.find_one({"_id": oid})
    if not existing:
        raise NotFoundError(f"Driver with ID '{driver_id}' not found.")
        
    active_rides = database.rides.count_documents({
        "driver_id": oid,
        "status": {"$in": ["requested", "accepted", "in_progress"]}
    })
    if active_rides > 0:
        raise ValidationError(f"Cannot delete driver: currently assigned to {active_rides} active ride(s).")
        
    database.drivers.delete_one({"_id": oid})
    return True


def get_all_drivers_dropdown(db=None) -> List[Dict[str, str]]:
    """Return lightweight list for selectboxes."""
    database = db if db is not None else get_db()
    cursor = database.drivers.find({}, {"name": 1, "vehicle_type": 1, "vehicle_number": 1}).sort("name", 1)
    return [
        {
            "_id": str(d["_id"]),
            "label": f"{d.get('name', 'N/A')} - {d.get('vehicle_type', '')} ({d.get('vehicle_number', '')})"
        }
        for d in cursor
    ]
