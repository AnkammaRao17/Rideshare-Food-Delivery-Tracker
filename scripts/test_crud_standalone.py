import sys, os
sys.path.insert(0, os.path.abspath("."))
from db import get_db
from services.rides_service import create_ride
from services.orders_service import create_order
from services.drivers_service import create_driver
from services.restaurants_service import create_restaurant
from services.users_service import create_user
import uuid

def main():
    db = get_db()
    user = db.users.find_one()
    driver = db.drivers.find_one()
    restaurant = db.restaurants.find_one()

    print(f"Sample User: {user['_id']}")
    print(f"Sample Driver: {driver['_id']}")
    print(f"Sample Restaurant: {restaurant['_id']}")

    # 1. Test create_ride
    try:
        r = create_ride({
            "user_id": str(user["_id"]),
            "driver_id": str(driver["_id"]),
            "pickup_location": "MG Road Metro Station",
            "dropoff_location": "Airport Terminal 2",
            "distance_km": 8.5,
            "fare": 320.0,
            "status": "requested"
        })
        print(f"Ride inserted successfully: ID={r['_id']}")
    except Exception as e:
        print(f"Ride insert failed: {type(e).__name__}: {e}")

    # 2. Test create_order
    try:
        o = create_order({
            "user_id": str(user["_id"]),
            "restaurant_id": str(restaurant["_id"]),
            "items": [{"item_name": "Butter Chicken", "quantity": 2, "price": 220.0}],
            "delivery_fee": 40.0,
            "total_amount": 480.0,
            "status": "placed"
        })
        print(f"Order inserted successfully: ID={o['_id']}")
    except Exception as e:
        print(f"Order insert failed: {type(e).__name__}: {e}")

    # 3. Test create_driver
    try:
        d = create_driver({
            "name": "Test Driver " + str(uuid.uuid4())[:6],
            "phone": "+91-987" + str(uuid.uuid4().int)[:7],
            "vehicle_type": "Sedan",
            "vehicle_number": "KA01AB" + str(uuid.uuid4().int)[:4],
            "rating": 4.8,
            "availability": True
        })
        print(f"Driver inserted successfully: ID={d['_id']}")
    except Exception as e:
        print(f"Driver insert failed: {type(e).__name__}: {e}")

    # 4. Test create_restaurant
    try:
        rest = create_restaurant({
            "name": "Test Rest " + str(uuid.uuid4())[:6],
            "cuisine": "North Indian",
            "location": "Indiranagar 100ft Road",
            "rating": 4.5,
            "is_active": True
        })
        print(f"Restaurant inserted successfully: ID={rest['_id']}")
    except Exception as e:
        print(f"Restaurant insert failed: {type(e).__name__}: {e}")

    # 5. Test create_user
    try:
        u = create_user({
            "name": "Test User",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+91-912" + str(uuid.uuid4().int)[:7]
        })
        print(f"User inserted successfully: ID={u['_id']}")
    except Exception as e:
        print(f"User insert failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
