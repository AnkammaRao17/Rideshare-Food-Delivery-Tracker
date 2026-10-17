"""
Data Validation and Testing Page.
Demonstrates database-level schema constraints, application-level business rules,
and includes an interactive live Pytest test runner.
"""

import streamlit as st
import pandas as pd
import subprocess
import sys
from bson import ObjectId

from services.users_service import create_user
from services.rides_service import create_ride
from services.orders_service import create_order
from models.validation import (
    ValidationError,
    DuplicateRecordError,
    NotFoundError,
    validate_email,
    validate_rating,
    validate_positive_number
)
from db import get_db
from ui_components import (
    render_header,
    render_empty_state,
    inject_custom_css
)


import re
import time
from datetime import datetime, timezone
from config import MONGO_URI, DATABASE_NAME, COLLECTIONS


def render():
    inject_custom_css()
    render_header(
        "Validation & Testing",
        "Test database connectivity, schema constraints, boundary validations, and execute automated pytest suites.",
        "🛡️"
    )
    
    tab_diag, tab_interactive, tab_pytest = st.tabs([
        "🔬 Database Live Diagnostics",
        "🧪 Interactive Constraint Sandbox",
        "⚡ Live Pytest Suite Runner"
    ])
    
    # TAB 1: DATABASE LIVE DIAGNOSTICS
    with tab_diag:
        st.subheader("MongoDB Live Connectivity & CRUD Diagnostics")
        st.caption("Perform harmless end-to-end connection, latency, collection audit, and isolated insert/read-back tests.")
        
        # 1. Connection & URI Audit
        masked_uri = re.sub(r"://([^@]+)@", "://***:***@", MONGO_URI)
        c_diag1, c_diag2 = st.columns(2)
        with c_diag1:
            st.markdown(f"**Configured Database:** `{DATABASE_NAME}`")
            st.markdown(f"**Connection URI:** `{masked_uri}`")
        with c_diag2:
            try:
                db = get_db()
                start_ping = time.time()
                ping_res = db.command("ping")
                ping_ms = round((time.time() - start_ping) * 1000, 2)
                st.success(f"🟢 **MongoDB Ping Succeeded!** Latency: `{ping_ms} ms`")
            except Exception as e:
                st.error(f"🔴 **MongoDB Connection Failed:** {e}")
                
        st.markdown("---")
        
        # 2. Collections Status Audit
        st.markdown("##### 📁 Collections & Document Counts")
        try:
            db = get_db()
            col_list = db.list_collection_names()
            stats_list = []
            expected = ["users", "drivers", "rides", "restaurants", "food_orders"]
            for ec in expected:
                exists = ec in col_list
                cnt = db[ec].count_documents({}) if exists else 0
                stats_list.append({
                    "Collection": ec,
                    "Status": "✅ Present" if exists else "❌ Missing",
                    "Record Count": f"{cnt:,}",
                    "Has Schema Validator": "✅ Yes" if exists and db.command({"listCollections": 1, "filter": {"name": ec}})["cursor"]["firstBatch"][0].get("options", {}).get("validator") else "No"
                })
            st.dataframe(pd.DataFrame(stats_list), use_container_width=True, hide_index=True)
        except Exception as ex:
            st.error(f"Failed to inspect collections: {ex}")
            
        st.markdown("---")
        
        # 3. Isolated Controlled Insert & Read-Back Test
        st.markdown("##### 🧪 Controlled Test Insert & Read-Back (Isolated Collection)")
        st.caption("Writes an isolated document into `_diagnostic_health_checks`, verifies `inserted_id`, and immediately reads it back.")
        
        col_test1, col_test2 = st.columns([2, 1])
        with col_test1:
            if st.button("🚀 Run Live Test Insert & Read-Back", type="primary", key="diag_run_test_btn"):
                try:
                    db = get_db()
                    diag_col = db["_diagnostic_health_checks"]
                    
                    test_doc = {
                        "test_timestamp": datetime.now(timezone.utc),
                        "purpose": "Live end-to-end write and read-back diagnostic",
                        "status": "active_test",
                        "test_value": 42.0
                    }
                    
                    # Execute Insert
                    t0 = time.time()
                    ins_res = diag_col.insert_one(test_doc)
                    insert_time_ms = round((time.time() - t0) * 1000, 2)
                    
                    if not ins_res.inserted_id:
                        st.error("❌ Insert operation failed: MongoDB returned no inserted_id.")
                    else:
                        st.success(f"✅ **Insert Succeeded!** MongoDB assigned ID: `{ins_res.inserted_id}` ({insert_time_ms} ms)")
                        
                        # Execute Read-Back
                        t1 = time.time()
                        read_back = diag_col.find_one({"_id": ins_res.inserted_id})
                        read_time_ms = round((time.time() - t1) * 1000, 2)
                        
                        if read_back and read_back["_id"] == ins_res.inserted_id:
                            st.success(f"✅ **Read-Back Verified!** Document retrieved intact in `{read_time_ms} ms`.")
                            with st.expander("📄 View Retrieved Test Document Payload"):
                                st.json({
                                    "_id": str(read_back["_id"]),
                                    "test_timestamp": str(read_back["test_timestamp"]),
                                    "purpose": read_back["purpose"],
                                    "status": read_back["status"],
                                    "test_value": read_back["test_value"]
                                })
                        else:
                            st.error("❌ Read-Back verification failed: Document not found in collection.")
                except Exception as ex:
                    st.error(f"❌ Test operation threw an exception: {ex}")
                    
        with col_test2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🧹 Clean Up Diagnostic Records", key="diag_clean_btn", type="secondary"):
                try:
                    db = get_db()
                    del_res = db["_diagnostic_health_checks"].delete_many({})
                    st.info(f"Cleared {del_res.deleted_count} test diagnostic records.")
                except Exception as ex:
                    st.error(f"Cleanup error: {ex}")

    # TAB 2: INTERACTIVE CONSTRAINT SANDBOX
    with tab_interactive:
        st.subheader("2. Interactive Constraint Validation Sandbox")
        st.caption("Select a scenario to trigger and observe how the system rejects invalid states with clean, actionable error messages.")
        
        scenario = st.selectbox(
            "Select Validation Scenario to Test",
            [
                "1. Reject Duplicate Customer Email (Unique Index & App Layer)",
                "2. Reject Malformed Email Address (Regex Pattern)",
                "3. Reject Negative Ride Distance or Fare (Range Bounds)",
                "4. Reject Out-of-Range Rating (Valid: 1.0 - 5.0)",
                "5. Reject Foreign Key Reference to Non-Existent Customer or Driver",
                "6. Reject Food Order with Empty Items Array"
            ]
        )
        
        st.markdown("---")
        
        # Scenario 1: Duplicate Email
        if "1. Reject Duplicate Customer Email" in scenario:
            st.markdown("#### Test Unique Email Constraint")
            st.write("Attempting to insert a customer with an existing registered email:")
            
            try:
                db = get_db()
                existing_user = db.users.find_one()
                test_email = existing_user["email"] if existing_user else "raji.prasad@example.in"
            except Exception:
                test_email = "raji.prasad@example.in"
            
            st.code(f"""create_user({{'name': 'Duplicate Customer', 'email': '{test_email}', 'phone': '+91-9876543210'}})""", language="python")
            
            if st.button("Trigger Duplicate Email Insertion", type="primary"):
                try:
                    create_user({"name": "Duplicate Customer", "email": test_email, "phone": "+91-9876543210"})
                    st.error("Error: Expected DuplicateRecordError but insertion succeeded!")
                except DuplicateRecordError as de:
                    st.success(f"✅ Handled successfully! Caught DuplicateRecordError: {de}")
                except Exception as ex:
                    st.warning(f"Caught database error: {ex}")

        # Scenario 2: Malformed Email
        elif "2. Reject Malformed Email Address" in scenario:
            st.markdown("#### Test Email Format Validation")
            malformed_input = st.text_input("Enter test email string", value="invalid-email-without-at-sign")
            
            if st.button("Validate Email", type="primary"):
                try:
                    validate_email(malformed_input)
                    st.error("Validation failed to reject invalid email.")
                except ValidationError as ve:
                    st.success(f"✅ Rejected by regex validation: {ve}")

        # Scenario 3: Negative Ride Distance or Fare
        elif "3. Reject Negative Ride Distance or Fare" in scenario:
            st.markdown("#### Test Numeric Boundary Validation")
            c1, c2 = st.columns(2)
            with c1:
                test_dist = st.number_input("Test Distance (km)", value=-10.0, step=1.0)
            with c2:
                test_fare = st.number_input("Test Fare (₹)", value=-50.0, step=5.0)
                
            if st.button("Submit Ride Validation", type="primary"):
                try:
                    validate_positive_number(test_dist, "distance_km", allow_zero=False)
                    validate_positive_number(test_fare, "fare", allow_zero=True)
                    st.error("Validation failed to reject negative numbers.")
                except ValidationError as ve:
                    st.success(f"✅ Rejected negative value: {ve}")

        # Scenario 4: Rating Bounds
        elif "4. Reject Out-of-Range Rating" in scenario:
            st.markdown("#### Test Rating Range [1.0, 5.0]")
            test_r = st.number_input("Test Rating", value=6.5, step=0.5)
            
            if st.button("Validate Rating", type="primary"):
                try:
                    validate_rating(test_r)
                    st.error("Validation failed to catch out of bounds rating.")
                except ValidationError as ve:
                    st.success(f"✅ Rejected out-of-range rating: {ve}")

        # Scenario 5: Missing Foreign Key
        elif "5. Reject Foreign Key Reference" in scenario:
            st.markdown("#### Test Foreign Key Integrity")
            st.write("Attempting to create a ride referencing non-existent ObjectIds:")
            
            fake_user = str(ObjectId())
            fake_driver = str(ObjectId())
            st.code(f"""
            create_ride({{
                "user_id": "{fake_user}",
                "driver_id": "{fake_driver}",
                "pickup_location": "Airport",
                "dropoff_location": "Hotel",
                "distance_km": 10.0,
                "fare": 200.0,
                "status": "requested"
            }})
            """, language="python")
            
            if st.button("Trigger Missing Foreign Key", type="primary"):
                try:
                    create_ride({
                        "user_id": fake_user,
                        "driver_id": fake_driver,
                        "pickup_location": "Airport",
                        "dropoff_location": "Hotel",
                        "distance_km": 10.0,
                        "fare": 200.0,
                        "status": "requested"
                    })
                    st.error("Failed to catch missing foreign key!")
                except NotFoundError as nfe:
                    st.success(f"✅ Caught relational reference violation: {nfe}")

        # Scenario 6: Empty Items Array
        elif "6. Reject Food Order with Empty Items Array" in scenario:
            st.markdown("#### Test Order Items Schema Requirement")
            st.write("Attempting to create a food order with an empty items array `items: []`:")
            
            try:
                db = get_db()
                user_doc = db.users.find_one()
                rest_doc = db.restaurants.find_one()
            except Exception:
                user_doc, rest_doc = None, None
            
            if user_doc and rest_doc:
                if st.button("Trigger Empty Items Insertion", type="primary"):
                    try:
                        create_order({
                            "user_id": str(user_doc["_id"]),
                            "restaurant_id": str(rest_doc["_id"]),
                            "items": [],
                            "delivery_fee": 30.0,
                            "status": "placed"
                        })
                        st.error("Order creation with empty items should have failed!")
                    except ValidationError as ve:
                        st.success(f"✅ Blocked empty items payload: {ve}")
            else:
                st.info("Please seed data to test this scenario.")

    # TAB 2: LIVE PYTEST RUNNER
    with tab_pytest:
        st.subheader("2. Run Automated Pytest Suite")
        st.markdown("""
        Click below to execute the complete automated test suite (`tests/test_crud.py`, `tests/test_validation.py`,
        `tests/test_aggregation.py`, `tests/test_indexes.py`) against the isolated test database `rideshare_delivery_test_db`.
        """)
        
        if st.button("▶️ Execute Full Pytest Suite Live", type="primary"):
            with st.spinner("Running automated pytest tests in child process..."):
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v"],
                    capture_output=True,
                    text=True
                )
                
                if proc.returncode == 0:
                    st.success("🎉 All test modules executed and PASSED successfully!")
                else:
                    st.error(f"Test run finished with exit code {proc.returncode}")
                    
                st.code(proc.stdout, language="bash")
                if proc.stderr:
                    st.warning(proc.stderr)


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
