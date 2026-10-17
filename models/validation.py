"""
Application-level data validation and business rules.
Ensures data integrity before sending commands to MongoDB.
"""

import re
from datetime import datetime, timezone
from bson import ObjectId
from config import RIDE_STATUSES, ORDER_STATUSES, VEHICLE_TYPES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


class ValidationError(Exception):
    """Custom exception raised when application-level validation fails."""
    pass


class NotFoundError(Exception):
    """Custom exception raised when a referenced or queried document does not exist."""
    pass


class DuplicateRecordError(Exception):
    """Custom exception raised when a unique constraint would be violated."""
    pass


def validate_object_id(oid_val, field_name="id") -> ObjectId:
    """Validate and convert input to BSON ObjectId."""
    if isinstance(oid_val, ObjectId):
        return oid_val
    if not oid_val or not isinstance(oid_val, str):
        raise ValidationError(f"{field_name} must be a valid 24-character hexadecimal string.")
    oid_val = oid_val.strip()
    if not ObjectId.is_valid(oid_val):
        raise ValidationError(f"{field_name} '{oid_val}' is not a valid MongoDB ObjectId.")
    return ObjectId(oid_val)


def validate_email(email: str) -> str:
    """Validate email format."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required and must be text.")
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        raise ValidationError(f"Invalid email address format: '{email}'.")
    return email


def validate_phone(phone: str) -> str:
    """Validate phone number string."""
    if not phone or not isinstance(phone, str):
        raise ValidationError("Phone number is required.")
    phone = phone.strip()
    if not PHONE_REGEX.match(phone):
        raise ValidationError(f"Invalid phone number format: '{phone}'.")
    return phone


def validate_rating(rating) -> float:
    """Validate rating is a float between 1.0 and 5.0."""
    try:
        val = float(rating)
    except (ValueError, TypeError):
        raise ValidationError("Rating must be a numeric value.")
    if not (1.0 <= val <= 5.0):
        raise ValidationError(f"Rating must be between 1.0 and 5.0. Got: {val}")
    return round(val, 1)


def validate_positive_number(val, field_name: str, allow_zero: bool = False) -> float:
    """Validate numeric value is positive (or non-negative if allow_zero is True)."""
    try:
        num = float(val)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a numeric value.")
    if allow_zero:
        if num < 0:
            raise ValidationError(f"{field_name} cannot be negative. Got: {num}")
    else:
        if num <= 0:
            raise ValidationError(f"{field_name} must be greater than zero. Got: {num}")
    return round(num, 2)


def validate_user_payload(data: dict) -> dict:
    """Validate payload for creating or updating a user."""
    name = str(data.get("name") or "").strip()
    if not name or len(name) < 2:
        raise ValidationError("Name must have at least 2 characters.")
    
    email = validate_email(data.get("email", ""))
    phone = validate_phone(data.get("phone", ""))
    
    return {
        "name": name,
        "email": email,
        "phone": phone
    }


def validate_driver_payload(data: dict) -> dict:
    """Validate payload for creating or updating a driver."""
    name = str(data.get("name") or "").strip()
    if not name or len(name) < 2:
        raise ValidationError("Driver name must have at least 2 characters.")
    
    phone = validate_phone(data.get("phone", ""))
    vehicle_type = str(data.get("vehicle_type") or "").strip()
    if not vehicle_type:
        raise ValidationError("Vehicle type is required.")
        
    vehicle_number = str(data.get("vehicle_number") or "").strip().upper()
    if not vehicle_number or len(vehicle_number) < 3:
        raise ValidationError("Vehicle number must be at least 3 characters.")
        
    rating = validate_rating(data.get("rating", 5.0))
    availability = bool(data.get("availability", True))
    
    return {
        "name": name,
        "phone": phone,
        "vehicle_type": vehicle_type,
        "vehicle_number": vehicle_number,
        "rating": rating,
        "availability": availability
    }


def validate_ride_payload(data: dict, db=None) -> dict:
    """
    Validate payload for creating or updating a ride.
    Optionally checks foreign keys in DB if db is provided.
    """
    user_id = validate_object_id(data.get("user_id"), "user_id")
    driver_id = validate_object_id(data.get("driver_id"), "driver_id")
    
    if db is not None:
        if not db.users.find_one({"_id": user_id}):
            raise NotFoundError(f"User with ID {user_id} does not exist.")
        if not db.drivers.find_one({"_id": driver_id}):
            raise NotFoundError(f"Driver with ID {driver_id} does not exist.")
            
    pickup = str(data.get("pickup_location") or "").strip()
    if not pickup or len(pickup) < 2:
        raise ValidationError("Pickup location must have at least 2 characters.")
        
    dropoff = str(data.get("dropoff_location") or "").strip()
    if not dropoff or len(dropoff) < 2:
        raise ValidationError("Dropoff location must have at least 2 characters.")
        
    distance_km = validate_positive_number(data.get("distance_km"), "distance_km", allow_zero=False)
    fare = validate_positive_number(data.get("fare"), "fare", allow_zero=True)
    
    status = data.get("status", "requested")
    if status not in RIDE_STATUSES:
        raise ValidationError(f"Invalid ride status '{status}'. Must be one of {RIDE_STATUSES}")
        
    completed_at = data.get("completed_at")
    if status == "completed" and not completed_at:
        completed_at = datetime.now(timezone.utc)
    elif status != "completed":
        completed_at = None

    return {
        "user_id": user_id,
        "driver_id": driver_id,
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "distance_km": distance_km,
        "fare": fare,
        "status": status,
        "completed_at": completed_at
    }


def validate_restaurant_payload(data: dict) -> dict:
    """Validate payload for restaurant."""
    name = str(data.get("name") or "").strip()
    if not name or len(name) < 2:
        raise ValidationError("Restaurant name must have at least 2 characters.")
        
    cuisine = str(data.get("cuisine") or "").strip()
    if not cuisine:
        raise ValidationError("Cuisine is required.")
        
    location = str(data.get("location") or "").strip()
    if not location or len(location) < 2:
        raise ValidationError("Location must have at least 2 characters.")
        
    rating = validate_rating(data.get("rating", 4.0))
    is_active = bool(data.get("is_active", True))
    
    return {
        "name": name,
        "cuisine": cuisine,
        "location": location,
        "rating": rating,
        "is_active": is_active
    }


def validate_order_items(items: list) -> list:
    """Validate order items list."""
    if not items or not isinstance(items, list):
        raise ValidationError("Order must contain at least one item.")
    
    validated_items = []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValidationError(f"Item #{idx} is invalid.")
        name = item.get("item_name", "").strip()
        if not name:
            raise ValidationError(f"Item #{idx} requires an item_name.")
        try:
            qty = int(item.get("quantity", 1))
        except (ValueError, TypeError):
            raise ValidationError(f"Item #{idx} quantity must be an integer.")
        if qty < 1:
            raise ValidationError(f"Item #{idx} quantity must be >= 1.")
            
        price = validate_positive_number(item.get("price", 0), f"Item #{idx} price", allow_zero=True)
        validated_items.append({
            "item_name": name,
            "quantity": qty,
            "price": price
        })
    return validated_items


def validate_food_order_payload(data: dict, db=None) -> dict:
    """Validate payload for food orders."""
    user_id = validate_object_id(data.get("user_id"), "user_id")
    restaurant_id = validate_object_id(data.get("restaurant_id"), "restaurant_id")
    
    if db is not None:
        if not db.users.find_one({"_id": user_id}):
            raise NotFoundError(f"User with ID {user_id} does not exist.")
        if not db.restaurants.find_one({"_id": restaurant_id}):
            raise NotFoundError(f"Restaurant with ID {restaurant_id} does not exist.")
            
    items = validate_order_items(data.get("items", []))
    
    # Calculate or validate total amount
    calculated_subtotal = sum(i["quantity"] * i["price"] for i in items)
    delivery_fee = validate_positive_number(data.get("delivery_fee", 30.0), "delivery_fee", allow_zero=True)
    
    total_amount = data.get("total_amount")
    if total_amount is not None:
        total_amount = validate_positive_number(total_amount, "total_amount", allow_zero=True)
    else:
        total_amount = round(calculated_subtotal + delivery_fee, 2)
        
    status = data.get("status", "placed")
    if status not in ORDER_STATUSES:
        raise ValidationError(f"Invalid order status '{status}'. Must be one of {ORDER_STATUSES}")
        
    delivered_at = data.get("delivered_at")
    if status == "delivered" and not delivered_at:
        delivered_at = datetime.now(timezone.utc)
    elif status != "delivered":
        delivered_at = None
        
    return {
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "items": items,
        "total_amount": total_amount,
        "delivery_fee": delivery_fee,
        "status": status,
        "delivered_at": delivered_at
    }
