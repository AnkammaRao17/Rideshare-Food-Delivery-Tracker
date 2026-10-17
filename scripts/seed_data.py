"""
Seed script for generating realistic synthetic data for Rideshare & Food Delivery Tracker.
Configurable via command line flags or runnable as a standalone script.
"""

import sys
import os
import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path so modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from faker import Faker
from bson import ObjectId
from db import get_db, init_db, reset_db
from config import (
    RIDE_STATUSES,
    ORDER_STATUSES,
    VEHICLE_TYPES,
    CUISINE_TYPES,
    DATABASE_NAME
)

fake = Faker()
Faker.seed(42)
random.seed(42)

INDIAN_CUSTOMERS = [
    "Raji Prasad", "Abhi Kumar", "Yaswanth Reddy", "Priya Sharma",
    "Rahul Verma", "Sneha Patel", "Ananya Rao", "Arjun Nair",
    "Kavya Reddy", "Sai Krishna", "Divya Venkatesh", "Vikram Malhotra",
    "Meera Krishnan", "Aditya Joshi", "Pooja Hegde", "Siddharth Rao",
    "Deepika Narayanan", "Manoj Tiwari", "Karthik Raja", "Swathi Naidu",
    "Vamsi Krishna", "Harini Murthy", "Pradeep Varma", "Shreya Sen",
    "Nikhil Aggarwal", "Varun Chawla", "Tarun Roy", "Ishaan Roy",
    "Bhavana Menon", "Tanvi Kulkarni", "Aravind Swamy", "Sowmya Rani",
    "Tejaswini S", "Kishore Babu", "Gayathri Devi", "Sanjay Dutt",
    "Lakshmi Narayana", "Padma Priya", "Rohan Gupta", "Sandhya R"
]

INDIAN_DRIVERS = [
    "Ravi Kumar", "Suresh Reddy", "Kiran Prasad", "Mahesh Yadav",
    "Arjun Sharma", "Naveen Rao", "Rohit Verma", "Pavan Kumar",
    "Santosh Nayak", "Ganesh Murthy", "Venkat Raman", "Anil Chauhan",
    "Harish Gowda", "Prasad Babu", "Chiranjeevi Naidu", "Balakrishna Reddy",
    "Nagendra Varma", "Apparao K", "Satyanarayana M", "Laxman Rao",
    "Ramu Somesh", "Dhanraj Goud", "Babu Jagjivan", "Raghuveer Singh"
]

INDIAN_RESTAURANTS = [
    ("Spice Garden", "North Indian", "Gachibowli, Hyderabad"),
    ("Andhra Ruchulu", "South Indian", "Banjara Hills, Hyderabad"),
    ("Raji's Kitchen", "South Indian", "Jubilee Hills, Hyderabad"),
    ("Hyderabad Biryani House", "North Indian", "Hitec City, Hyderabad"),
    ("South Indian Cafe", "South Indian", "Indiranagar, Bengaluru"),
    ("Tandoori Junction", "North Indian", "Koramangala, Bengaluru"),
    ("Desi Dhaba", "North Indian", "Whitefield, Bengaluru"),
    ("Green Leaf Restaurant", "South Indian", "T. Nagar, Chennai"),
    ("Paradise Bawarchi", "North Indian", "Secunderabad, Hyderabad"),
    ("Swagath Gourmet", "Continental", "Adyar, Chennai"),
    ("Chutneys Classic", "South Indian", "Anna Nagar, Chennai"),
    ("Rayalaseema Ruchulu", "South Indian", "Benz Circle, Vijayawada"),
    ("Udupi Grand", "South Indian", "MG Road, Vijayawada"),
    ("Pista House", "Bakery & Desserts", "Charminar, Hyderabad"),
    ("Coastal Bay Bistro", "Chinese", "Beach Road, Visakhapatnam"),
    ("Sri Kanya Comfort", "South Indian", "Siripuram, Visakhapatnam")
]

RESTAURANT_MENU_ITEMS = {
    "North Indian": [
        ("Chicken Biryani", 320.0), ("Paneer Butter Masala", 260.0),
        ("Dal Makhani", 220.0), ("Butter Naan", 50.0),
        ("Chicken 65", 280.0), ("Veg Fried Rice", 190.0)
    ],
    "South Indian": [
        ("Masala Dosa", 90.0), ("Idli and Vada", 80.0),
        ("Ghee Roast Dosa", 130.0), ("Filter Coffee", 40.0),
        ("Curd Rice", 100.0), ("Veg Thali", 220.0)
    ],
    "Chinese": [
        ("Hakka Noodles", 200.0), ("Chilli Chicken", 270.0),
        ("Veg Manchurian", 210.0), ("Schezwan Fried Rice", 230.0),
        ("Spring Rolls", 170.0)
    ],
    "Italian": [
        ("Margherita Pizza", 360.0), ("Penne Arrabbiata", 310.0),
        ("White Sauce Pasta", 330.0), ("Garlic Bread with Cheese", 150.0)
    ],
    "American": [
        ("Classic Smash Burger", 250.0), ("Crispy Chicken Burger", 270.0),
        ("Loaded French Fries", 140.0), ("Chocolate Milkshake", 150.0)
    ],
    "Continental": [
        ("Grilled Chicken Breast", 410.0), ("Mushroom Stroganoff", 350.0),
        ("Fish and Chips", 370.0)
    ],
    "Bakery & Desserts": [
        ("Gulab Jamun (2 pcs)", 70.0), ("Red Velvet Cupcake", 110.0),
        ("Blueberry Cheesecake", 220.0), ("Double Ka Meetha", 90.0)
    ]
}

CITY_LOCATIONS = [
    "Hitec City, Hyderabad", "Jubilee Hills, Hyderabad", "Banjara Hills, Hyderabad", "Gachibowli, Hyderabad",
    "Koramangala, Bengaluru", "Indiranagar, Bengaluru", "Whitefield, Bengaluru", "MG Road, Bengaluru",
    "T. Nagar, Chennai", "Anna Nagar, Chennai", "Adyar, Chennai", "Velachery, Chennai",
    "Benz Circle, Vijayawada", "MG Road, Vijayawada", "Bhavanipuram, Vijayawada",
    "Beach Road, Visakhapatnam", "Siripuram, Visakhapatnam", "MVP Colony, Visakhapatnam",
    "Madhapur, Hyderabad", "Kondapur, Hyderabad"
]


def seed_database(
    num_users: int = 40,
    num_drivers: int = 20,
    num_restaurants: int = 15,
    num_rides: int = 150,
    num_orders: int = 150,
    reset: bool = False,
    db_name: str = None
):
    """Seed database with synthetic data."""
    target_db_name = db_name or DATABASE_NAME
    print(f"--- Seeding Database: {target_db_name} ---")
    
    if reset:
        print("Resetting database...")
        reset_db(target_db_name, confirm=True)
    else:
        init_db(target_db_name)
        
    db = get_db(target_db_name)
    
    # 1. Seed Users
    print(f"Creating {num_users} users with authentic Indian names...")
    user_docs = []
    base_time = datetime.now(timezone.utc)
    existing_emails = set(db.users.distinct("email"))
    
    for i in range(num_users):
        name = INDIAN_CUSTOMERS[i % len(INDIAN_CUSTOMERS)]
        clean_prefix = name.lower().replace(" ", ".")
        email = f"{clean_prefix}.{random.randint(100, 9999)}@gmail.com"
        while email in existing_emails:
            email = f"{clean_prefix}.{random.randint(100, 9999)}@gmail.com"
        existing_emails.add(email)
        
        phone = f"+91-{random.choice(['98', '99', '97', '94', '93', '91', '89', '70'])}{random.randint(10000000, 99999999)}"
        created_days_ago = random.randint(15, 120)
        user_docs.append({
            "_id": ObjectId(),
            "name": name,
            "email": email,
            "phone": phone,
            "created_at": base_time - timedelta(days=created_days_ago, minutes=random.randint(0, 1440))
        })
    if user_docs:
        db.users.insert_many(user_docs)
    user_ids = db.users.distinct("_id")
    print(f"Total users in DB: {len(user_ids)}")
    
    # 2. Seed Drivers
    print(f"Creating {num_drivers} drivers with authentic Indian names & vehicle plates...")
    driver_docs = []
    state_codes = ["TS", "AP", "KA", "TN", "DL"]
    series_codes = ["AB", "CD", "EF", "GH", "KL", "MN", "XY"]
    
    for i in range(num_drivers):
        name = INDIAN_DRIVERS[i % len(INDIAN_DRIVERS)]
        phone = f"+91-{random.choice(['98', '99', '97', '94', '93', '91', '89', '70'])}{random.randint(10000000, 99999999)}"
        st_code = random.choice(state_codes)
        rto_num = f"{random.randint(1, 14):02d}"
        series = random.choice(series_codes)
        num_part = f"{random.randint(1000, 9999)}"
        plate = f"{st_code}{rto_num}{series}{num_part}"
        
        driver_docs.append({
            "_id": ObjectId(),
            "name": name,
            "phone": phone,
            "vehicle_type": random.choice(VEHICLE_TYPES),
            "vehicle_number": plate,
            "rating": round(random.uniform(4.0, 5.0), 1),
            "availability": random.choice([True, True, True, False])
        })
    if driver_docs:
        db.drivers.insert_many(driver_docs)
    driver_ids = db.drivers.distinct("_id")
    print(f"Total drivers in DB: {len(driver_ids)}")
    
    # 3. Seed Restaurants
    print(f"Creating {num_restaurants} restaurants with Indian eateries & cuisines...")
    restaurant_docs = []
    for i in range(num_restaurants):
        preset = INDIAN_RESTAURANTS[i % len(INDIAN_RESTAURANTS)]
        restaurant_docs.append({
            "_id": ObjectId(),
            "name": preset[0] if i < len(INDIAN_RESTAURANTS) else f"{preset[0]} Express",
            "cuisine": preset[1],
            "location": preset[2],
            "rating": round(random.uniform(4.0, 4.9), 1),
            "is_active": random.choice([True, True, True, False])
        })
    if restaurant_docs:
        db.restaurants.insert_many(restaurant_docs)
    restaurants = list(db.restaurants.find({}, {"_id": 1, "cuisine": 1}))
    print(f"Total restaurants in DB: {len(restaurants)}")
    
    # 4. Seed Rides
    print(f"Creating {num_rides} rides...")
    ride_docs = []
    status_weights = [0.05, 0.05, 0.05, 0.75, 0.10]  # requested, accepted, in_progress, completed, cancelled
    
    for _ in range(num_rides):
        status = random.choices(RIDE_STATUSES, weights=status_weights)[0]
        dist = round(random.uniform(1.5, 38.0), 2)
        base_rate = random.choice([15.0, 18.0, 22.0])
        fare = round(dist * base_rate + random.uniform(20.0, 50.0), 2)
        
        days_ago = random.randint(1, 90)
        created_at = base_time - timedelta(days=days_ago, minutes=random.randint(0, 1440))
        
        completed_at = None
        if status == "completed":
            completed_at = created_at + timedelta(minutes=random.randint(15, 60))
            
        pickup = random.choice(CITY_LOCATIONS)
        dropoff = random.choice([loc for loc in CITY_LOCATIONS if loc != pickup])
        
        ride_docs.append({
            "_id": ObjectId(),
            "user_id": random.choice(user_ids),
            "driver_id": random.choice(driver_ids),
            "pickup_location": pickup,
            "dropoff_location": dropoff,
            "distance_km": dist,
            "fare": fare,
            "status": status,
            "created_at": created_at,
            "completed_at": completed_at
        })
    if ride_docs:
        db.rides.insert_many(ride_docs)
    print(f"Total rides created: {len(ride_docs)}")
    
    # 5. Seed Food Orders
    print(f"Creating {num_orders} food orders...")
    order_docs = []
    order_status_weights = [0.05, 0.05, 0.05, 0.75, 0.10] # placed, preparing, out_for_delivery, delivered, cancelled
    
    for _ in range(num_orders):
        rest = random.choice(restaurants)
        cuisine = rest.get("cuisine", "North Indian")
        menu = RESTAURANT_MENU_ITEMS.get(cuisine, RESTAURANT_MENU_ITEMS["North Indian"])
        
        num_items = random.randint(1, 4)
        chosen_items = random.sample(menu, min(num_items, len(menu)))
        order_items = []
        for item_name, price in chosen_items:
            order_items.append({
                "item_name": item_name,
                "quantity": random.randint(1, 3),
                "price": price
            })
            
        subtotal = sum(i["quantity"] * i["price"] for i in order_items)
        delivery_fee = round(random.choice([25.0, 35.0, 45.0, 50.0]), 2)
        total_amount = round(subtotal + delivery_fee, 2)
        
        status = random.choices(ORDER_STATUSES, weights=order_status_weights)[0]
        days_ago = random.randint(1, 90)
        created_at = base_time - timedelta(days=days_ago, minutes=random.randint(0, 1440))
        
        delivered_at = None
        if status == "delivered":
            delivered_at = created_at + timedelta(minutes=random.randint(25, 65))
            
        order_docs.append({
            "_id": ObjectId(),
            "user_id": random.choice(user_ids),
            "restaurant_id": rest["_id"],
            "items": order_items,
            "total_amount": total_amount,
            "delivery_fee": delivery_fee,
            "status": status,
            "created_at": created_at,
            "delivered_at": delivered_at
        })
    if order_docs:
        db.food_orders.insert_many(order_docs)
    print(f"Total food orders created: {len(order_docs)}")
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic data for Rideshare & Food Delivery Tracker.")
    parser.add_argument("--users", type=int, default=50, help="Number of users to generate")
    parser.add_argument("--drivers", type=int, default=25, help="Number of drivers to generate")
    parser.add_argument("--restaurants", type=int, default=15, help="Number of restaurants to generate")
    parser.add_argument("--rides", type=int, default=180, help="Number of rides to generate")
    parser.add_argument("--orders", type=int, default=180, help="Number of food orders to generate")
    parser.add_argument("--reset", action="store_true", help="Drop existing database and re-initialize")
    parser.add_argument("--db", type=str, default=None, help="Target database name")
    
    args = parser.parse_args()
    seed_database(
        num_users=args.users,
        num_drivers=args.drivers,
        num_restaurants=args.restaurants,
        num_rides=args.rides,
        num_orders=args.orders,
        reset=args.reset,
        db_name=args.db
    )
