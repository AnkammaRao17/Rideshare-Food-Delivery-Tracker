"""
Index Management Page.
Inspect existing indexes, analyze index sizes, create custom compound indexes, and drop indexes safely.
"""

import streamlit as st
import pandas as pd
from pymongo import ASCENDING, DESCENDING

from services.index_service import (
    list_collection_indexes,
    create_index_on_collection,
    drop_index_from_collection,
    get_all_collections_index_summary
)
from db import get_db
from ui_components import (
    render_header,
    render_empty_state,
    inject_custom_css
)


def render():
    inject_custom_css()
    render_header(
        "Indexes",
        "Inspect B-Tree indexes, monitor storage footprint, build compound keys, and evaluate read/write trade-offs.",
        "🗂️"
    )
    
    # 1. Index Storage Overview
    st.subheader("📊 Collection Index Storage Overview")
    try:
        summary = get_all_collections_index_summary()
        summary_rows = []
        for col_name, stats in summary.items():
            summary_rows.append({
                "Collection Name": col_name,
                "Documents Count": f"{stats.get('count', 0):,}",
                "Data Size (KB)": f"{stats.get('size_kb', 0):,.2f}",
                "Index Size (KB)": f"{stats.get('total_index_size_kb', 0):,.2f}",
                "Active B-Tree Indexes": stats.get("num_indexes", 0)
            })
        df_sum = pd.DataFrame(summary_rows)
        st.dataframe(df_sum, use_container_width=True, hide_index=True)
    except Exception as ex:
        st.error(f"Error fetching index summary: {ex}")

    st.markdown("---")

    # 2. Detailed Index Inspector
    st.subheader("🔍 Inspect Indexes by Collection")
    selected_col = st.selectbox("Select Collection to Inspect", ["rides", "food_orders", "users", "drivers", "restaurants"])
    
    try:
        col_indexes = list_collection_indexes(selected_col)
        idx_display = []
        for idx in col_indexes:
            keys_str = ", ".join([f"{k}: {'ASC' if v==1 else 'DESC'}" for k, v in idx["keys"]])
            idx_display.append({
                "Index Name": idx["name"],
                "Key Definition": keys_str,
                "Unique Constraint": "✅ Unique" if idx.get("unique") else "No"
            })
        df_idx = pd.DataFrame(idx_display)
        st.dataframe(df_idx, use_container_width=True, hide_index=True)

        # Drop Index Option
        st.markdown("##### 🗑️ Drop a Custom Index")
        droppable = [i["Index Name"] for i in idx_display if i["Index Name"] != "_id_"]
        if droppable:
            c_drop1, c_drop2 = st.columns([3, 1])
            with c_drop1:
                idx_to_drop = st.selectbox("Select non-primary index to drop", options=droppable, key="drop_idx_sel")
            with c_drop2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Drop Index", type="secondary"):
                    try:
                        drop_index_from_collection(selected_col, idx_to_drop)
                        st.success(f"Index '{idx_to_drop}' successfully dropped from '{selected_col}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to drop index: {e}")
        else:
            st.caption("No custom non-primary indexes available to drop.")
    except Exception as ex:
        st.error(f"Error querying collection indexes: {ex}")

    st.markdown("---")

    # 3. Create Custom Compound Index
    st.subheader("➕ Create a Custom Index")
    with st.form("create_index_form"):
        col_target = st.selectbox("Target Collection", ["rides", "food_orders", "users", "drivers", "restaurants"], key="ci_col")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            field_1 = st.text_input("First Field *", placeholder="e.g. status", value="status")
            dir_1 = st.selectbox("Field 1 Direction", ["ASCENDING (1)", "DESCENDING (-1)"])
        with c2:
            field_2 = st.text_input("Second Field (Optional for Compound)", placeholder="e.g. fare", value="fare")
            dir_2 = st.selectbox("Field 2 Direction", ["DESCENDING (-1)", "ASCENDING (1)"])
        with c3:
            custom_name = st.text_input("Custom Index Name (Optional)", placeholder="idx_rides_status_fare")
            is_unique = st.checkbox("Unique Constraint", value=False)
            
        submit_idx = st.form_submit_button("🚀 Build B-Tree Index in MongoDB", type="primary")
        if submit_idx:
            if not field_1.strip():
                st.error("First field name is required.")
            else:
                d1_val = 1 if "ASCENDING" in dir_1 else -1
                keys = [(field_1.strip(), d1_val)]
                
                if field_2.strip():
                    d2_val = 1 if "ASCENDING" in dir_2 else -1
                    keys.append((field_2.strip(), d2_val))
                    
                try:
                    name_created = create_index_on_collection(
                        col_target,
                        keys,
                        unique=is_unique,
                        name=custom_name if custom_name.strip() else None
                    )
                    st.success(f"Index '{name_created}' created successfully on '{col_target}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create index: {e}")

    st.markdown("---")

    # 4. Educational Guidance: Trade-offs
    st.subheader("📚 Indexing Trade-offs: Read Latency vs Write Amplification")
    st.markdown("""
    | Operational Metric | Without Index (`COLLSCAN`) | With B-Tree Index (`IXSCAN`) |
    | :--- | :--- | :--- |
    | **Search Complexity** | **$O(N)$** Full collection sequential scan | **$O(\log N)$** B-Tree logarithmic search |
    | **RAM Working Set** | Minimal (indexes not buffered in RAM) | Moderate (active indexes cached in WiredTiger RAM) |
    | **Write Performance** | **Fastest** (append document directly) | **Slower** (all B-Trees must be updated on insert/update/delete) |
    | **Storage Footprint** | Document payload only | Raw data + approximately 15% - 35% index overhead |
    | **Optimal Use Case** | Ad-hoc analytics or write-heavy append logs | High-frequency queries, equality filters, range queries & joins |
    """)


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
