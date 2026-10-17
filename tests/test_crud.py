"""
Unit and integration tests for CRUD operations.
"""

import pytest
from bson import ObjectId
from services.users_service import (
    create_user, get_user_by_id, get_users, update_user, delete_user
)
from services.drivers_service import (
    create_driver, get_driver_by_id, get_drivers, update_driver, delete_driver
)
from services.restaurants_service import (
    create_restaurant, get_restaurant_by_id, get_restaurants, update_restaurant, delete_restaurant
)
from services.rides_service import (
    create_ride, get_ride_by_id, get_rides, update_ride, delete_ride
)
from services.orders_service import (
    create_order, get_order_by_id, get_orders, update_order, delete_order
)
from models.validation import NotFoundError, ValidationError, DuplicateRecordError


def test_user_crud(test_db):
    """Test full CRUD lifecycle for User."""
    email = f"user_{ObjectId()}@test.com"
    payload = {"name": "Test User", "email": email, "phone": "+1-800-555-0100"}
    
    # 1. Create
    created = create_user(payload, db=test_db)
    assert created["_id"] is not None
    assert created["email"] == email
    
    # 2. Read
    fetched = get_user_by_id(created["_id"], db=test_db)
    assert fetched["name"] == "Test User"
    
    # 3. Update
    updated = update_user(created["_id"], {"name": "Test User Updated", "email": email, "phone": "+1-800-555-0199"}, db=test_db)
    assert updated["name"] == "Test User Updated"
    assert updated["phone"] == "+1-800-555-0199"
    
    # 4. List / Pagination
    users, total = get_users(search="Test User", db=test_db)
    assert total >= 1
    assert any(u["_id"] == created["_id"] for u in users)
    
    # 5. Delete
    deleted = delete_user(created["_id"], db=test_db)
    assert deleted is True
    
    with pytest.raises(NotFoundError):
        get_user_by_id(created["_id"], db=test_db)


def test_driver_crud(test_db):
    """Test full CRUD lifecycle for Driver."""
    payload = {
        "name": "David Driver",
        "phone": "+1-555-9988",
        "vehicle_type": "SUV",
        "vehicle_number": "KA05CD9999",
        "rating": 4.7,
        "availability": True
    }
    
    created = create_driver(payload, db=test_db)
    assert created["_id"] is not None
    assert created["vehicle_type"] == "SUV"
    
    fetched = get_driver_by_id(created["_id"], db=test_db)
    assert fetched["name"] == "David Driver"
    
    updated = update_driver(created["_id"], {**payload, "rating": 4.9, "availability": False}, db=test_db)
    assert updated["rating"] == 4.9
    assert updated["availability"] is False
    
    deleted = delete_driver(created["_id"], db=test_db)
    assert deleted is True


def test_restaurant_crud(test_db):
    """Test full CRUD lifecycle for Restaurant."""
    payload = {
        "name": "Pasta Fresca",
        "cuisine": "Italian",
        "location": "Downtown Square",
        "rating": 4.6,
        "is_active": True
    }
    
    created = create_restaurant(payload, db=test_db)
    assert created["_id"] is not None
    
    fetched = get_restaurant_by_id(created["_id"], db=test_db)
    assert fetched["cuisine"] == "Italian"
    
    updated = update_restaurant(created["_id"], {**payload, "name": "Pasta Fresca & Wine"}, db=test_db)
    assert updated["name"] == "Pasta Fresca & Wine"
    
    deleted = delete_restaurant(created["_id"], db=test_db)
    assert deleted is True


def test_ride_crud(test_db, sample_user, sample_driver):
    """Test full CRUD lifecycle for Ride including joins and status update."""
    payload = {
        "user_id": str(sample_user["_id"]),
        "driver_id": str(sample_driver["_id"]),
        "pickup_location": "Airport Terminal 1",
        "dropoff_location": "Grand Hyatt Hotel",
        "distance_km": 15.5,
        "fare": 450.0,
        "status": "requested"
    }
    
    # 1. Create
    created = create_ride(payload, db=test_db)
    assert created["_id"] is not None
    assert created["status"] == "requested"
    
    # 2. Read with joins
    fetched = get_ride_by_id(created["_id"], db=test_db)
    assert fetched["pickup_location"] == "Airport Terminal 1"
    assert fetched.get("user") is not None
    assert fetched["user"]["name"] == sample_user["name"]
    
    # 3. Update to completed
    updated = update_ride(created["_id"], {**payload, "status": "completed"}, db=test_db)
    assert updated["status"] == "completed"
    assert updated.get("completed_at") is not None
    
    # 4. Query listing
    rides, total = get_rides(status="completed", db=test_db)
    assert total >= 1
    
    # 5. Delete
    deleted = delete_ride(created["_id"], db=test_db)
    assert deleted is True
    
    with pytest.raises(NotFoundError):
        get_ride_by_id(created["_id"], db=test_db)


def test_food_order_crud(test_db, sample_user, sample_restaurant):
    """Test full CRUD lifecycle for Food Order."""
    payload = {
        "user_id": str(sample_user["_id"]),
        "restaurant_id": str(sample_restaurant["_id"]),
        "items": [
            {"item_name": "Butter Chicken", "quantity": 1, "price": 320.0},
            {"item_name": "Garlic Naan", "quantity": 2, "price": 60.0}
        ],
        "delivery_fee": 40.0,
        "status": "placed"
    }
    
    # 1. Create
    created = create_order(payload, db=test_db)
    assert created["_id"] is not None
    assert created["total_amount"] == 480.0  # (320 + 120 + 40)
    
    # 2. Read with joins
    fetched = get_order_by_id(created["_id"], db=test_db)
    assert fetched["user"]["name"] == sample_user["name"]
    assert fetched["restaurant"]["name"] == sample_restaurant["name"]
    
    # 3. Update to delivered
    updated = update_order(created["_id"], {**payload, "status": "delivered"}, db=test_db)
    assert updated["status"] == "delivered"
    assert updated.get("delivered_at") is not None
    
    # 4. Delete
    deleted = delete_order(created["_id"], db=test_db)
    assert deleted is True
