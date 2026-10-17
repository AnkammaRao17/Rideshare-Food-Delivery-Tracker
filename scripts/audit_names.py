import sys, os
sys.path.insert(0, os.path.abspath("."))
from db import get_db

db = get_db()
print(f"Total Users: {db.users.count_documents({})}")
for u in db.users.find({}, {"name": 1, "email": 1}):
    print(f"  User: {u['_id']} | {u.get('name')} | {u.get('email')}")

print(f"\nTotal Drivers: {db.drivers.count_documents({})}")
for d in db.drivers.find({}, {"name": 1, "vehicle_number": 1}):
    print(f"  Driver: {d['_id']} | {d.get('name')} | {d.get('vehicle_number')}")

print(f"\nTotal Restaurants: {db.restaurants.count_documents({})}")
for r in db.restaurants.find({}, {"name": 1, "cuisine": 1}):
    print(f"  Restaurant: {r['_id']} | {r.get('name')} | {r.get('cuisine')}")
