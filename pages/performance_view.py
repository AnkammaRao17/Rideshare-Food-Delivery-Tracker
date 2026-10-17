"""
Query Performance and Optimization Page.
Runs genuine MongoDB cursor.explain("executionStats"), compares COLLSCAN vs IXSCAN,
and benchmarks query execution against configurable synthetic datasets.
"""

import streamlit as st
import pandas as pd
import json

from services.performance_service import (
    analyze_query_plan,
    run_index_comparison_benchmark,
    seed_synthetic_benchmark_collection
)
from db import get_db
from ui_components import (
    render_header,
    render_kpi,
    render_empty_state,
    inject_custom_css
)


def render():
    inject_custom_css()
    render_header(
        "Performance",
        "Inspect query execution plans with MongoDB executionStats, comparing COLLSCAN vs IXSCAN performance.",
        "📈"
    )
    
    st.markdown("""
    > [!NOTE]
    > **WiredTiger Query Execution Stages:**
    > - **COLLSCAN (Collection Scan):** MongoDB inspects every single document on disk in sequential order ($O(N)$ linear complexity).
    > - **IXSCAN (Index Scan):** MongoDB traverses an in-memory B-Tree index ($O(\log N)$ logarithmic complexity) and extracts pointers before fetching only matching documents.
    """)
    
    tab_explain, tab_benchmark = st.tabs(["🔍 Live Query Explain", "⏱️ Rigorous Before & After Benchmark"])
    
    # TAB 1: LIVE QUERY EXPLAIN
    with tab_explain:
        st.subheader("1. Inspect Winning Plan on Development Collections")
        
        c1, c2 = st.columns(2)
        with c1:
            col_target = st.selectbox("Collection", ["rides", "food_orders", "users", "drivers"], key="exp_col")
        with c2:
            query_type = st.selectbox(
                "Filter Scenario",
                ["Filter by Status (Indexed)", "Filter by Unindexed Field (e.g. pickup_location)", "Range on Fare / Total Amount (₹)"]
            )
            
        if query_type == "Filter by Status (Indexed)":
            test_filter = {"status": "completed" if col_target == "rides" else "delivered"}
        elif query_type == "Filter by Unindexed Field (e.g. pickup_location)":
            test_filter = {"pickup_location": "Downtown Central"} if col_target == "rides" else {"phone": "+1-555-0199"}
        else:
            test_filter = {"fare": {"$gt": 250.0}} if col_target == "rides" else {"total_amount": {"$gt": 400.0}}
            
        st.markdown(f"**Target PyMongo Query:** `db.{col_target}.find({json.dumps(test_filter)})`")
        
        if st.button("🚀 Run explain('executionStats')", type="primary"):
            try:
                plan = analyze_query_plan(col_target, test_filter)
                
                # Metrics Cards
                m1, m2, m3, m4 = st.columns(4)
                render_kpi(m1, "Winning Plan Stage", plan["stage"], f"Index: {plan['index_name']}", "#0D9488" if "IXSCAN" in plan["stage"] else "#DC2626")
                render_kpi(m2, "Docs Examined", f"{plan['totalDocsExamined']:,}", "Documents read from storage", "#0D9488" if plan["totalDocsExamined"] <= plan["nReturned"] else "#F59E0B")
                render_kpi(m3, "Keys Examined", f"{plan['totalKeysExamined']:,}", "B-Tree keys inspected", "#3B82F6")
                render_kpi(m4, "Execution Time", f"{plan['executionTimeMillis']} ms", f"{plan['nReturned']} documents returned", "#10B981")
                
                # Detailed Breakdown
                st.markdown("#### Execution Summary Breakdown")
                st.write(f"- **Execution Strategy:** `{plan['stage']}`")
                st.write(f"- **Total Documents Examined in Storage:** `{plan['totalDocsExamined']:,}`")
                st.write(f"- **Index Keys Traversed in B-Tree:** `{plan['totalKeysExamined']:,}`")
                st.write(f"- **Target Documents Returned to Client:** `{plan['nReturned']:,}`")
                
                if plan["totalDocsExamined"] > 0 and plan["nReturned"] > 0:
                    ratio = round(plan["totalDocsExamined"] / plan["nReturned"], 2)
                    st.write(f"- **Selectivity Ratio:** `{ratio}:1` (Lower is better; 1:1 is optimal index selectivity).")
                    
                with st.expander("📄 View Full MongoDB Explain JSON Payload"):
                    st.json(plan["raw_explain"])
            except Exception as e:
                st.error(f"Failed to execute explain plan: {e}")

    # TAB 2: RIGOROUS BEFORE & AFTER BENCHMARK
    with tab_benchmark:
        st.subheader("2. Controlled Before-and-After Index Benchmark")
        st.markdown("""
        This benchmark tests a query, removes the target index to capture an unindexed baseline (`COLLSCAN`),
        builds the B-Tree index, and measures the exact reduction in `totalDocsExamined` and `executionTimeMillis`.
        """)
        
        st.markdown("##### Step A: Synthetic High-Volume Dataset Generation")
        st.caption("On small collections (< 500 documents), modern SSDs and RAM cache execute queries in 0ms. Generating 5,000 to 20,000 synthetic records highlights genuine disk and B-Tree advantages.")
        
        c_vol1, c_vol2 = st.columns([2, 1])
        with c_vol1:
            records_count = st.select_slider(
                "Synthetic Records to Generate in 'benchmark_rides'",
                options=[2000, 5000, 10000, 20000],
                value=5000
            )
        with c_vol2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Generate Synthetic Benchmark Data"):
                with st.spinner(f"Inserting {records_count:,} synthetic documents into MongoDB..."):
                    res = seed_synthetic_benchmark_collection(records_count)
                    st.success(f"Generated {res['total_inserted']:,} test records in '{res['collection']}'!")
                    
        try:
            db = get_db()
            benchmark_count = db["benchmark_rides"].count_documents({})
        except Exception:
            benchmark_count = 0
            
        st.write(f"**Current 'benchmark_rides' Document Count:** `{benchmark_count:,}`")
        
        st.markdown("---")
        st.markdown("##### Step B: Execute Benchmark Comparison")
        
        if benchmark_count == 0:
            render_empty_state("Benchmark Collection Empty", "Click 'Generate Synthetic Benchmark Data' above to populate the benchmark collection.", "⚙️")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                query_field = st.selectbox("Field to Benchmark", ["driver_code", "status", "pickup_zone"])
                field_val = "DRV-0042" if query_field == "driver_code" else ("completed" if query_field == "status" else "Downtown")
            with col_b2:
                st.text_input("Target Value", value=field_val, disabled=True)
                
            if st.button("🚀 Run Live Before vs After Index Comparison", type="primary"):
                with st.spinner("Executing baseline scan, building B-Tree index, and executing indexed scan..."):
                    bench_res = run_index_comparison_benchmark(
                        collection_name="benchmark_rides",
                        query_filter={query_field: field_val},
                        index_keys=[(query_field, 1)],
                        index_name=f"idx_bench_{query_field}"
                    )
                    
                    b_base = bench_res["baseline"]
                    b_idx = bench_res["indexed"]
                    
                    st.success("Benchmark completed using genuine MongoDB executionStats!")
                    
                    # Comparison Columns
                    comp1, comp2 = st.columns(2)
                    with comp1:
                        st.markdown("### 🔴 Baseline (Without Index)")
                        st.error(f"**Strategy:** {b_base['stage']}")
                        st.write(f"- **Docs Examined:** `{b_base['totalDocsExamined']:,}`")
                        st.write(f"- **Keys Examined:** `{b_base['totalKeysExamined']:,}`")
                        st.write(f"- **Execution Time:** `{b_base['executionTimeMillis']} ms`")
                        st.write(f"- **Returned Documents:** `{b_base['nReturned']:,}`")
                        
                    with comp2:
                        st.markdown("### 🟢 Optimized (With B-Tree Index)")
                        st.success(f"**Strategy:** {b_idx['stage']}")
                        st.write(f"- **Docs Examined:** `{b_idx['totalDocsExamined']:,}`")
                        st.write(f"- **Keys Examined:** `{b_idx['totalKeysExamined']:,}`")
                        st.write(f"- **Execution Time:** `{b_idx['executionTimeMillis']} ms`")
                        st.write(f"- **Returned Documents:** `{b_idx['nReturned']:,}`")
                        
                    st.markdown("---")
                    st.markdown("### 📈 Efficiency Gain Report")
                    pct_saved = bench_res["docs_pct_reduction"]
                    st.info(f"""
                    **Benchmark Insights:**
                    - **Documents Skipped:** The B-Tree index prevented reading **{bench_res['docs_saved']:,} unnecessary documents** from disk.
                    - **I/O Overhead Reduction:** **{pct_saved}% reduction** in documents examined!
                    - **Algorithm Shift:** Shifted from linear full scan **$O(N)$** to targeted logarithmic lookup **$O(\log N)$**.
                    """)


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
