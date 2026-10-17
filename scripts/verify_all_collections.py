import sys, os
sys.path.insert(0, os.path.abspath("."))
import uuid
from datetime import datetime, timezone
from db import get_db, ping_db, get_client
from config import MONGO_URI, DATABASE_NAME
from services.rides_service import create_ride
from services.orders_service import create_order
from services.drivers_service import create_driver
from services.restaurants_service import create_restaurant
from services.users_service import create_user

def main():
    print("=" * 60)
    print("STEP 1: VERIFY CONNECTION")
    print("=" * 60)
    client = get_client()
    ok, info = ping_db()
    
    # Safe URI check (masking credentials if present)
    safe_uri = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
    print(f"Configured MONGO_URI (safe): {safe_uri}")
    print(f"Configured DATABASE_NAME: {DATABASE_NAME}")
    print(f"Active Ping: {ok} -> {info}")
    
    db = get_db()
    print(f"Connected DB Name: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
    
    print("\n" + "=" * 60)
    print("STEP 2: DIAGNOSTIC ISOLATED TEST INSERT")
    print("=" * 60)
    diag_col = db["_diagnostic_isolated_test"]
    diag_doc = {
        "diagnostic_id": str(uuid.uuid4()),
        "test": "isolated_connection_verification",
        "created_at": datetime.now(timezone.utc)
    }
    diag_res = diag_col.insert_one(diag_doc)
    diag_readback = diag_col.find_one({"_id": diag_res.inserted_id})
    print(f"Diagnostic Collection: {diag_col.name}")
    print(f"Diagnostic Inserted ID: {diag_res.inserted_id}")
    print(f"Diagnostic Read-back match: {diag_readback is not None and diag_readback['_id'] == diag_res.inserted_id}")
    diag_col.delete_one({"_id": diag_res.inserted_id})
    print("Diagnostic test document cleaned up successfully.")

    print("\n" + "=" * 60)
    print("STEP 3 & 4 & 6: INSERTION AND READ-BACK TEST FOR 5 COLLECTIONS")
    print("=" * 60)

    # Pre-fetch existing valid reference documents
    user_ref = db.users.find_one()
    driver_ref = db.drivers.find_one()
    rest_ref = db.restaurants.find_one()

    results = []

    # 1. rides
    c_rides_before = db.rides.count_documents({})
    try:
        r = create_ride({
            "user_id": str(user_ref["_id"]),
            "driver_id": str(driver_ref["_id"]),
            "pickup_location": "Brigade Road, Bangalore",
            "dropoff_location": "Koramangala Sony Signal",
            "distance_km": 6.8,
            "fare": 240.0,
            "status": "requested"
        })
        r_id = r["_id"]
        r_readback = db.rides.find_one({"_id": r["_id"] if isinstance(r["_id"], str) else r["_id"]})
        if not r_readback:
            from bson import ObjectId
            r_readback = db.rides.find_one({"_id": ObjectId(str(r["_id"]))})
        c_rides_after = db.rides.count_documents({})
        results.append({
            "Collection": "rides",
            "Before": c_rides_before,
            "Insert Succeeded": True,
            "Inserted ID": str(r_id),
            "Read-Back Succeeded": r_readback is not None,
            "After": c_rides_after,
            "Error": None
        })
    except Exception as e:
        results.append({
            "Collection": "rides",
            "Before": c_rides_before,
            "Insert Succeeded": False,
            "Inserted ID": None,
            "Read-Back Succeeded": False,
            "After": db.rides.count_documents({}),
            "Error": str(e)
        })

    # 2. food_orders
    c_orders_before = db.food_orders.count_documents({})
    try:
        o = create_order({
            "user_id": str(user_ref["_id"]),
            "restaurant_id": str(rest_ref["_id"]),
            "items": [
                {"item_name": "Paneer Butter Masala", "quantity": 1, "price": 280.0},
                {"item_name": "Garlic Naan", "quantity": 2, "price": 60.0}
            ],
            "delivery_fee": 35.0,
            "total_amount": 435.0,
            "status": "placed"
        })
        o_id = o["_id"]
        from bson import ObjectId
        o_readback = db.food_orders.find_one({"_id": ObjectId(str(o_id))})
        c_orders_after = db.food_orders.count_documents({})
        results.append({
            "Collection": "food_orders",
            "Before": c_orders_before,
            "Insert Succeeded": True,
            "Inserted ID": str(o_id),
            "Read-Back Succeeded": o_readback is not None,
            "After": c_orders_after,
            "Error": None
        })
    except Exception as e:
        results.append({
            "Collection": "food_orders",
            "Before": c_orders_before,
            "Insert Succeeded": False,
            "Inserted ID": None,
            "Read-Back Succeeded": False,
            "After": db.food_orders.count_documents({}),
            "Error": str(e)
        })

    # 3. drivers
    c_drivers_before = db.drivers.count_documents({})
    try:
        d = create_driver({
            "name": "Verified Driver " + str(uuid.uuid4())[:6],
            "phone": "+91-987" + str(uuid.uuid4().int)[:7],
            "vehicle_type": "EV Sedan",
            "vehicle_number": "KA03EV" + str(uuid.uuid4().int)[:4],
            "rating": 4.9,
            "availability": True
        })
        d_id = d["_id"]
        from bson import ObjectId
        d_readback = db.drivers.find_one({"_id": ObjectId(str(d_id))})
        c_drivers_after = db.drivers.count_documents({})
        results.append({
            "Collection": "drivers",
            "Before": c_drivers_before,
            "Insert Succeeded": True,
            "Inserted ID": str(d_id),
            "Read-Back Succeeded": d_readback is not None,
            "After": c_drivers_after,
            "Error": None
        })
    except Exception as e:
        results.append({
            "Collection": "drivers",
            "Before": c_drivers_before,
            "Insert Succeeded": False,
            "Inserted ID": None,
            "Read-Back Succeeded": False,
            "After": db.drivers.count_documents({}),
            "Error": str(e)
        })

    # 4. restaurants
    c_rests_before = db.restaurants.count_documents({})
    try:
        rest = create_restaurant({
            "name": "Verified Bistro " + str(uuid.uuid4())[:6],
            "cuisine": "Continental",
            "location": "Lavelle Road, Bangalore",
            "rating": 4.7,
            "is_active": True
        })
        rest_id = rest["_id"]
        from bson import ObjectId
        rest_readback = db.restaurants.find_one({"_id": ObjectId(str(rest_id))})
        c_rests_after = db.restaurants.count_documents({})
        results.append({
            "Collection": "restaurants",
            "Before": c_rests_before,
            "Insert Succeeded": True,
            "Inserted ID": str(rest_id),
            "Read-Back Succeeded": rest_readback is not None,
            "After": c_rests_after,
            "Error": None
        })
    except Exception as e:
        results.append({
            "Collection": "restaurants",
            "Before": c_rests_before,
            "Insert Succeeded": False,
            "Inserted ID": None,
            "Read-Back Succeeded": False,
            "After": db.restaurants.count_documents({}),
            "Error": str(e)
        })

    # 5. users
    c_users_before = db.users.count_documents({})
    try:
        u = create_user({
            "name": "Verified Passenger",
            "email": f"verified_{uuid.uuid4().hex[:6]}@example.in",
            "phone": "+91-912" + str(uuid.uuid4().int)[:7]
        })
        u_id = u["_id"]
        from bson import ObjectId
        u_readback = db.users.find_one({"_id": ObjectId(str(u_id))})
        c_users_after = db.users.count_documents({})
        results.append({
            "Collection": "users",
            "Before": c_users_before,
            "Insert Succeeded": True,
            "Inserted ID": str(u_id),
            "Read-Back Succeeded": u_readback is not None,
            "After": c_users_after,
            "Error": None
        })
    except Exception as e:
        results.append({
            "Collection": "users",
            "Before": c_users_before,
            "Insert Succeeded": False,
            "Inserted ID": None,
            "Read-Back Succeeded": False,
            "After": db.users.count_documents({}),
            "Error": str(e)
        })

    print(f"\n{'Collection':<14} | {'Before':<6} | {'Insert OK':<9} | {'Read-Back OK':<12} | {'After':<6} | {'Inserted ID':<24} | {'Error'}")
    print("-" * 105)
    for res in results:
        err_str = res['Error'] if res['Error'] else 'None'
        print(f"{res['Collection']:<14} | {res['Before']:<6} | {str(res['Insert Succeeded']):<9} | {str(res['Read-Back Succeeded']):<12} | {res['After']:<6} | {str(res['Inserted ID']):<24} | {err_str}")

if __name__ == "__main__":
    main()
