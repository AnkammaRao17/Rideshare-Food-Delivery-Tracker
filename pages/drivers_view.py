"""
Drivers Management Page.
Full CRUD: View records, Add new, Edit existing, View details, and Delete with confirmation.
"""

import streamlit as st
import pandas as pd

from services.drivers_service import (
    create_driver, get_drivers, get_driver_by_id, update_driver, delete_driver
)
from config import VEHICLE_TYPES
from models.validation import ValidationError, NotFoundError, DuplicateRecordError
from ui_components import (
    render_header,
    paginate_dataframe,
    render_empty_state,
    inject_custom_css
)


def render():
    inject_custom_css()
    if "drivers_success_toast" in st.session_state:
        st.success(st.session_state.pop("drivers_success_toast"))
        
    render_header(
        "Drivers",
        "View, onboard, update, and manage driver partner records and vehicle fleet.",
        "🚖"
    )
    
    tab_list, tab_create = st.tabs(["📋 View Records", "➕ Add New"])
    
    # -------------------------------------------------------------
    # TAB 1: VIEW RECORDS
    # -------------------------------------------------------------
    with tab_list:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            search_query = st.text_input("🔍 Search Drivers (Name, Phone, Plate)", key="drv_search")
        with f2:
            vehicle_filter = st.selectbox("Vehicle Type", ["All"] + VEHICLE_TYPES, index=0, key="drv_veh")
        with f3:
            avail_filter = st.selectbox("Availability", ["All", "Available Only", "Offline Only"], index=0, key="drv_avail")
        with f4:
            min_rating = st.slider("Min Rating ⭐", 1.0, 5.0, 1.0, 0.1, key="drv_min_r")
            
        avail_val = None
        if avail_filter == "Available Only":
            avail_val = True
        elif avail_filter == "Offline Only":
            avail_val = False
            
        try:
            drivers, total_count = get_drivers(
                search=search_query,
                availability=avail_val,
                vehicle_type=vehicle_filter if vehicle_filter != "All" else None,
                min_rating=min_rating if min_rating > 1.0 else None,
                page=1,
                limit=300,
                sort_by="rating",
                sort_dir=-1
            )
        except Exception as e:
            st.error(f"Failed to query drivers from database: {e}")
            drivers, total_count = [], 0
            
        st.markdown(f"**Total Records Found:** `{total_count}`")
        
        if drivers:
            df = pd.DataFrame(drivers)[["_id", "name", "phone", "vehicle_type", "vehicle_number", "rating", "availability"]]
            df["availability"] = df["availability"].apply(lambda a: "🟢 Available" if a else "🔴 Offline")
            df.columns = ["Driver ID", "Full Name", "Phone", "Vehicle Type", "License Plate", "Rating ⭐", "Availability"]
            paginated_df = paginate_dataframe(df, page_size=10, key_prefix="drv_p")
            st.dataframe(paginated_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🔍 Select a Record to View, Edit, or Delete")
            
            selected_driver_id = st.selectbox(
                "Choose a driver record",
                options=[d["_id"] for d in drivers],
                format_func=lambda did: next((f"{d['name']} ({d['vehicle_type']} - {d['vehicle_number']}) | ⭐{d['rating']} | {'Available' if d.get('availability') else 'Offline'}" for d in drivers if d["_id"] == did), did),
                key="selected_driver_action"
            )
            
            if selected_driver_id:
                try:
                    driver_detail = get_driver_by_id(selected_driver_id)
                    col_view, col_edit = st.columns(2)
                    
                    with col_view:
                        st.markdown("#### 📄 Record Details")
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #0F9D8A;">
                            <p><b>Driver ID:</b> <code>{driver_detail['_id']}</code></p>
                            <p><b>Full Name:</b> {driver_detail['name']}</p>
                            <p><b>Phone:</b> {driver_detail['phone']}</p>
                            <p><b>Vehicle Type:</b> {driver_detail['vehicle_type']}</p>
                            <p><b>Vehicle Registration Number:</b> {driver_detail['vehicle_number']}</p>
                            <p><b>Rating:</b> ⭐ {driver_detail['rating']} / 5.0</p>
                            <p><b>Availability Status:</b> {'<span class="badge badge-completed">Available</span>' if driver_detail['availability'] else '<span class="badge badge-cancelled">Offline</span>'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("#### 🗑️ Delete Record")
                        confirm_del = st.checkbox("I confirm I want to permanently delete this driver record", key=f"del_chk_drv_{selected_driver_id}")
                        if st.button("Delete Driver Record", type="secondary", disabled=not confirm_del, key=f"del_btn_drv_{selected_driver_id}"):
                            try:
                                delete_driver(selected_driver_id)
                                st.success(f"Driver '{driver_detail['name']}' successfully removed!")
                                st.rerun()
                            except (ValidationError, NotFoundError) as e:
                                st.error(str(e))
                                
                    with col_edit:
                        st.markdown("#### ✏️ Edit Record")
                        with st.form("edit_driver_form"):
                            edit_name = st.text_input("Full Name", value=driver_detail["name"])
                            edit_phone = st.text_input("Phone Number", value=driver_detail["phone"])
                            edit_vtype = st.selectbox(
                                "Vehicle Type",
                                options=VEHICLE_TYPES,
                                index=VEHICLE_TYPES.index(driver_detail["vehicle_type"]) if driver_detail["vehicle_type"] in VEHICLE_TYPES else 0
                            )
                            edit_vnum = st.text_input("Vehicle Registration Number", value=driver_detail["vehicle_number"])
                            edit_rating = st.slider("Rating ⭐", 1.0, 5.0, float(driver_detail["rating"]), 0.1)
                            edit_avail = st.checkbox("Available for Trips", value=bool(driver_detail["availability"]))
                            
                            submit_edit = st.form_submit_button("💾 Save Changes", type="primary")
                            if submit_edit:
                                try:
                                    update_driver(selected_driver_id, {
                                        "name": edit_name,
                                        "phone": edit_phone,
                                        "vehicle_type": edit_vtype,
                                        "vehicle_number": edit_vnum,
                                        "rating": edit_rating,
                                        "availability": edit_avail
                                    })
                                    st.success("Driver updated successfully!")
                                    st.rerun()
                                except (ValidationError, NotFoundError, DuplicateRecordError) as e:
                                    st.error(str(e))
                except Exception as ex:
                    st.error(f"Error fetching driver details: {ex}")
        else:
            render_empty_state("No Drivers Found", "No driver profiles matched your search or filter settings.", "🚖")

    # -------------------------------------------------------------
    # TAB 2: ADD NEW
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Add a New Driver")
        with st.form("add_driver_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Full Name *", value="", placeholder="e.g. Ramesh Patel", key="add_drv_name")
                new_phone = st.text_input("Phone Number *", value="", placeholder="e.g. +91-9876543299", key="add_drv_phone")
                new_vtype = st.selectbox("Vehicle Type *", options=VEHICLE_TYPES, key="add_drv_vtype")
            with c2:
                new_vnum = st.text_input("Vehicle Registration Number *", value="", placeholder="e.g. KA05MN4321", key="add_drv_vnum")
                new_rating = st.slider("Rating", 1.0, 5.0, 4.8, 0.1, key="add_drv_rating")
                new_avail = st.checkbox("Availability (Available for Trips)", value=True, key="add_drv_avail")
                
            submit_add = st.form_submit_button("➕ Add Driver", type="primary")
            if submit_add:
                try:
                    clean_name = str(new_name or "").strip()
                    clean_phone = str(new_phone or "").strip()
                    clean_vnum = str(new_vnum or "").strip()
                    
                    new_d = create_driver({
                        "name": clean_name,
                        "phone": clean_phone,
                        "vehicle_type": new_vtype,
                        "vehicle_number": clean_vnum,
                        "rating": float(new_rating),
                        "availability": bool(new_avail)
                    })
                    st.session_state["recent_added_driver"] = new_d
                    st.session_state["drivers_success_toast"] = (
                        f"✅ **Driver '{new_d['name']}' successfully added & verified in MongoDB!** ID: `{new_d['_id']}` | "
                        f"Vehicle: {new_d['vehicle_type']} ({new_d['vehicle_number']}) | Phone: {new_d['phone']}"
                    )
                    st.rerun()
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(f"⚠️ Validation Error: {e}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    st.error(f"🔴 Database Operation Error: {type(ex).__name__}: {ex}")
                    print(f"DATABASE WRITE ERROR in add_driver: {ex}")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
