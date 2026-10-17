"""
MongoDB JSON Schema Validators for database-level validation.
These schemas are applied using create_collection or collMod in MongoDB.
"""

from config import RIDE_STATUSES, ORDER_STATUSES

USER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "phone", "created_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 100,
                "description": "User's full name (2-100 characters)"
            },
            "email": {
                "bsonType": "string",
                "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$",
                "description": "Valid email address format required"
            },
            "phone": {
                "bsonType": "string",
                "minLength": 7,
                "maxLength": 20,
                "description": "Phone number string"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp as BSON Date"
            }
        }
    }
}

DRIVER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "phone", "vehicle_type", "vehicle_number", "rating", "availability"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 100
            },
            "phone": {
                "bsonType": "string",
                "minLength": 7,
                "maxLength": 20
            },
            "vehicle_type": {
                "bsonType": "string"
            },
            "vehicle_number": {
                "bsonType": "string",
                "minLength": 3
            },
            "rating": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 1.0,
                "maximum": 5.0,
                "description": "Driver rating between 1.0 and 5.0"
            },
            "availability": {
                "bsonType": "bool",
                "description": "Whether the driver is currently available"
            }
        }
    }
}

RIDE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id", "driver_id", "pickup_location",
            "dropoff_location", "distance_km", "fare", "status", "created_at"
        ],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "user_id": {
                "bsonType": "objectId",
                "description": "Referenced user ObjectId"
            },
            "driver_id": {
                "bsonType": "objectId",
                "description": "Referenced driver ObjectId"
            },
            "pickup_location": {
                "bsonType": "string",
                "minLength": 2
            },
            "dropoff_location": {
                "bsonType": "string",
                "minLength": 2
            },
            "distance_km": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 0.01,
                "description": "Distance in kilometers (must be positive)"
            },
            "fare": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 0.0,
                "description": "Fare in local currency (must be positive)"
            },
            "status": {
                "enum": RIDE_STATUSES,
                "description": f"Status must be one of: {RIDE_STATUSES}"
            },
            "created_at": {
                "bsonType": "date"
            },
            "completed_at": {
                "bsonType": ["date", "null"]
            }
        }
    }
}

RESTAURANT_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "cuisine", "location", "rating", "is_active"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "name": {
                "bsonType": "string",
                "minLength": 2
            },
            "cuisine": {
                "bsonType": "string",
                "minLength": 2
            },
            "location": {
                "bsonType": "string",
                "minLength": 2
            },
            "rating": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 1.0,
                "maximum": 5.0
            },
            "is_active": {
                "bsonType": "bool"
            }
        }
    }
}

FOOD_ORDER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id", "restaurant_id", "items", "total_amount",
            "delivery_fee", "status", "created_at"
        ],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "user_id": {
                "bsonType": "objectId",
                "description": "Referenced user ObjectId"
            },
            "restaurant_id": {
                "bsonType": "objectId",
                "description": "Referenced restaurant ObjectId"
            },
            "items": {
                "bsonType": "array",
                "minItems": 1,
                "items": {
                    "bsonType": "object",
                    "required": ["item_name", "quantity", "price"],
                    "properties": {
                        "item_name": {"bsonType": "string", "minLength": 1},
                        "quantity": {"bsonType": ["int", "long"], "minimum": 1},
                        "price": {"bsonType": ["double", "int", "decimal"], "minimum": 0.0}
                    }
                }
            },
            "total_amount": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 0.0
            },
            "delivery_fee": {
                "bsonType": ["double", "int", "decimal"],
                "minimum": 0.0
            },
            "status": {
                "enum": ORDER_STATUSES,
                "description": f"Status must be one of: {ORDER_STATUSES}"
            },
            "created_at": {
                "bsonType": "date"
            },
            "delivered_at": {
                "bsonType": ["date", "null"]
            }
        }
    }
}

VALIDATORS = {
    "users": USER_VALIDATOR,
    "drivers": DRIVER_VALIDATOR,
    "rides": RIDE_VALIDATOR,
    "restaurants": RESTAURANT_VALIDATOR,
    "food_orders": FOOD_ORDER_VALIDATOR
}
