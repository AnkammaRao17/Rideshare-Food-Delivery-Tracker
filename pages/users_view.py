"""
Users Management Page.
Full CRUD: View records, Add new, Edit existing, View details, and Delete with confirmation.
"""

import streamlit as st
import pandas as pd

from services.users_service import (
    create_user, get_users, get_user_by_id, update_user, delete_user
)
from db import get_db
from models.validation import ValidationError, DuplicateRecordError, NotFoundError
from ui_components import (
    render_header,
    paginate_dataframe,
    render_empty_state,
    inject_custom_css
)


def render():
    inject_custom_css()
    if "users_success_toast" in st.session_state:
        st.success(st.session_state.pop("users_success_toast"))
        
    render_header(
        "Users",
        "View, register, edit, and manage registered user accounts.",
        "👥"
    )
    
    tab_list, tab_create = st.tabs(["📋 View Records", "➕ Add New"])
    
    # -------------------------------------------------------------
    # TAB 1: VIEW RECORDS
    # -------------------------------------------------------------
    with tab_list:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            search_query = st.text_input("🔍 Search Users (Name, Email, Phone)", key="users_search")
        with c2:
            sort_field = st.selectbox("Sort By", ["created_at", "name", "email"], index=0, key="u_sort_field")
        with c3:
            sort_dir = st.selectbox("Order", ["Descending (Newest)", "Ascending"], index=0, key="u_sort_dir")
            
        dir_val = -1 if "Descending" in sort_dir else 1
        
        try:
            users, total_count = get_users(
                search=search_query,
                page=1,
                limit=300,
                sort_by=sort_field,
                sort_dir=dir_val
            )
        except Exception as e:
            st.error(f"Error querying users: {e}")
            users, total_count = [], 0
            
        st.markdown(f"**Total Users Found:** `{total_count}`")
        
        if users:
            df = pd.DataFrame(users)[["_id", "name", "email", "phone", "created_at"]]
            df.columns = ["User ID", "User Name", "Email Address", "Phone Number", "Registered At"]
            paginated_df = paginate_dataframe(df, page_size=10, key_prefix="users_p")
            st.dataframe(paginated_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🔍 Select a User to View, Edit, or Delete")
            
            selected_user_id = st.selectbox(
                "Choose a user account",
                options=[u["_id"] for u in users],
                format_func=lambda uid: next((f"{u['name']} ({u['email']}) - Phone: {u['phone']}" for u in users if u["_id"] == uid), uid),
                key="selected_user_action"
            )
            
            if selected_user_id:
                try:
                    user_detail = get_user_by_id(selected_user_id)
                    col_view, col_edit = st.columns(2)
                    
                    with col_view:
                        st.markdown("#### 📄 User Details")
                        
                        db = get_db()
                        u_rides_count = db.rides.count_documents({"user_id": user_detail["_id"]})
                        u_orders_count = db.food_orders.count_documents({"user_id": user_detail["_id"]})
                        
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #0F9D8A;">
                            <p><b>User ID:</b> <code>{user_detail['_id']}</code></p>
                            <p><b>Full Name:</b> {user_detail['name']}</p>
                            <p><b>Email Address:</b> {user_detail['email']}</p>
                            <p><b>Phone Number:</b> {user_detail['phone']}</p>
                            <p><b>Registered At:</b> {user_detail['created_at']}</p>
                            <p><b>User Ride History:</b> <b>{u_rides_count} rides</b></p>
                            <p><b>User Order History:</b> <b>{u_orders_count} food orders</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("#### 🗑️ Delete User Record")
                        confirm_del = st.checkbox("I confirm I want to permanently delete this user account", key=f"del_chk_usr_{selected_user_id}")
                        if st.button("Delete User Record", type="secondary", disabled=not confirm_del, key=f"del_btn_usr_{selected_user_id}"):
                            try:
                                delete_user(selected_user_id)
                                st.success(f"User '{user_detail['name']}' successfully deleted!")
                                st.rerun()
                            except (ValidationError, NotFoundError) as e:
                                st.error(str(e))
                                
                    with col_edit:
                        st.markdown("#### ✏️ Edit User Record")
                        with st.form("edit_user_form"):
                            edit_name = st.text_input("User Name", value=user_detail["name"])
                            edit_email = st.text_input("Email Address", value=user_detail["email"])
                            edit_phone = st.text_input("Phone Number", value=user_detail["phone"])
                            
                            submit_edit = st.form_submit_button("💾 Save Changes", type="primary")
                            if submit_edit:
                                try:
                                    update_user(selected_user_id, {
                                        "name": edit_name,
                                        "email": edit_email,
                                        "phone": edit_phone
                                    })
                                    st.success("User profile updated successfully!")
                                    st.rerun()
                                except (ValidationError, NotFoundError, DuplicateRecordError) as e:
                                    st.error(str(e))
                except Exception as ex:
                    st.error(f"Error fetching user details: {ex}")
        else:
            render_empty_state("No Users Found", "No registered user accounts match your search criteria.", "👥")

    # -------------------------------------------------------------
    # TAB 2: ADD NEW
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Add a New User")
        with st.form("add_user_form"):
            new_name = st.text_input("User Full Name *", value="", placeholder="e.g. Raji Prasad", key="add_usr_name")
            new_email = st.text_input("Email Address *", value="", placeholder="e.g. raji.prasad@example.in", key="add_usr_email")
            new_phone = st.text_input("Phone Number *", value="", placeholder="e.g. +91-9876543211", key="add_usr_phone")
            
            submit_add = st.form_submit_button("➕ Add User", type="primary")
            if submit_add:
                try:
                    clean_name = str(new_name or "").strip()
                    clean_email = str(new_email or "").strip().lower()
                    clean_phone = str(new_phone or "").strip()
                    
                    new_u = create_user({
                        "name": clean_name,
                        "email": clean_email,
                        "phone": clean_phone
                    })
                    st.session_state["recent_added_user"] = new_u
                    st.session_state["users_success_toast"] = (
                        f"✅ **User '{new_u['name']}' successfully registered & verified in MongoDB!** ID: `{new_u['_id']}` | "
                        f"Email: {new_u['email']} | Phone: {new_u['phone']}"
                    )
                    st.rerun()
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(f"⚠️ Validation Error: {e}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    st.error(f"🔴 Database Operation Error: {type(ex).__name__}: {ex}")
                    print(f"DATABASE WRITE ERROR in add_user: {ex}")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
