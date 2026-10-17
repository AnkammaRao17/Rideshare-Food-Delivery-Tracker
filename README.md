# 🚖 Rideshare & Food Delivery Tracker

A full-stack operational intelligence platform and database engineering showcase built using **Python**, **MongoDB**, **PyMongo**, and **Streamlit**. 

This system models real-world multi-vertical on-demand logistics (combining on-demand ridesharing and multi-restaurant food delivery), demonstrating **production CRUD operations**, **advanced querying**, **multi-stage aggregation pipelines**, **MongoDB JSON Schema validation**, **indexing strategies**, and **rigorous `explain("executionStats")` query optimization**.

---

## 📑 Table of Contents
1. [Project Overview & Key Objectives](#-project-overview--key-objectives)
2. [Technology Stack](#-technology-stack)
3. [Database Architecture & Schema Design](#-database-architecture--schema-design)
4. [Installation & Local Setup](#-installation--local-setup)
5. [Database Seeding & Reset](#-database-seeding--reset)
6. [Launching the Web Dashboard](#-launching-the-web-dashboard)
7. [Running Automated Tests](#-running-automated-tests)
8. [Core Feature Showcase](#-core-feature-showcase)
   - [CRUD Operations & UI Management](#1-crud-operations--ui-management)
   - [Advanced Query Demonstrations](#2-advanced-query-demonstrations)
   - [Aggregation Pipelines](#3-aggregation-pipelines)
   - [Data Validation (Dual-Layer)](#4-data-validation-dual-layer)
   - [Index Management & Storage](#5-index-management--storage)
   - [Query Optimization (`COLLSCAN` vs `IXSCAN`)](#6-query-optimization-collscan-vs-ixscan)
9. [Query Optimization Benchmark Results](#-query-optimization-benchmark-results)
10. [Troubleshooting & Common Pitfalls](#-troubleshooting--common-pitfalls)
11. [College Project Presentation Script](#-college-project-presentation-script)

---

## 🎯 Project Overview & Key Objectives

Traditional database projects often model a single isolated domain. **Rideshare & Food Delivery Tracker** connects customers, drivers, restaurants, and transactions across two high-volume service verticals:
- **Ridesharing**: Point-to-point passenger transport with dynamic fares, distance calculation, vehicle assignments, and real-time trip status progression.
- **Food Delivery**: Multi-item restaurant orders with subdocument arrays, item quantities, delivery fees, and order status life-cycles.

### Core Engineering Goals:
- **Clean Relational Modeling in NoSQL**: Utilize BSON `ObjectId` references to link `users`, `drivers`, and `restaurants` while leveraging embedded subdocument arrays for order items.
- **Strict Data Validation**: Dual-layer protection using database-level MongoDB `$jsonSchema` validators alongside robust application-level Python validations.
- **Analytical Intelligence**: Execute multi-stage aggregation pipelines (`$match`, `$group`, `$lookup`, `$unwind`, `$project`, `$facet`) to calculate financial KPIs, revenue trends, and operational metrics.
- **Query Optimization**: Measure physical query execution plans via `explain("executionStats")`, contrasting unindexed Collection Scans (`COLLSCAN`) with B-Tree Index Scans (`IXSCAN`).

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Language** | Python | 3.13+ | Core business logic, validation rules, service layer |
| **Database Engine** | MongoDB Community / Atlas | 8.x / 7.x | Document database storage, B-Tree indexes, JSON Schema |
| **Database Driver** | PyMongo | 4.13+ | Connection pooling, aggregation pipelines, cursor explain |
| **User Interface** | Streamlit | 1.40+ | Modern multi-page interactive web application |
| **Analytics & Data** | Pandas | 2.3+ | Data manipulation, tabular formatting, pagination |
| **Visualizations** | Plotly Express & Graph Objects | 6.x / 7.x | Interactive revenue charts, status donuts, trend lines |
| **Synthetic Seeding** | Faker | 40.x | Realistic mock names, addresses, vehicles, and menus |
| **Testing Suite** | pytest | 9.x | Automated test coverage across CRUD, schemas, and queries |
| **Configuration** | python-dotenv | 1.x | Safe environment variable isolation |

---

## 🗄️ Database Architecture & Schema Design

Database Name: `rideshare_delivery_db` (Isolated test database: `rideshare_delivery_test_db`)

```
   +--------------------+               +--------------------+
   |       users        |               |      drivers       |
   +--------------------+               +--------------------+
   | _id: ObjectId      |<-------+      | _id: ObjectId      |<-------+
   | name: String       |        |      | name: String       |        |
   | email: String (UQ) |        |      | phone: String      |        |
   | phone: String      |        |      | vehicle_type: Str  |        |
   | created_at: Date   |        |      | vehicle_number: Str|        |
   +--------------------+        |      | rating: Double     |        |
                                 |      | availability: Bool |        |
                                 |      +--------------------+        |
                                 |                                    |
   +--------------------+        |      +--------------------+        |
   |    restaurants     |        |      |       rides        |        |
   +--------------------+        |      +--------------------+        |
   | _id: ObjectId      |<--+    |      | _id: ObjectId      |        |
   | name: String       |   |    +------| user_id: ObjectId  |        |
   | cuisine: String    |   |           +------| driver_id: ObjectId|        |
   | location: String   |   |           | pickup_loc: String |        |
   | rating: Double     |   |           | dropoff_loc: String|        |
   | is_active: Bool    |   |           | distance_km: Double|        |
   +--------------------+   |           | fare: Double       |        |
                            |           | status: String     |        |
                            |           | created_at: Date   |        |
                            |           | completed_at: Date |        |
   +--------------------+   |           +--------------------+        |
   |    food_orders     |   |                                         |
   +--------------------+   |                                         |
   | _id: ObjectId      |   |                                         |
   | user_id: ObjectId  |---+                                         |
   | restaurant_id: OID |---+                                         |
   | items: Array[Doc]  |                                             |
   |   - item_name: Str |                                             |
   |   - quantity: Int  |                                             |
   |   - price: Double  |                                             |
   | total_amount: Dbl  |                                             |
   | delivery_fee: Dbl  |                                             |
   | status: String     |                                             |
   | created_at: Date   |                                             |
   | delivered_at: Date |                                             |
   +--------------------+                                             |
```

### Monetary Values Representation
All monetary values (`fare`, `price`, `delivery_fee`, `total_amount`) are stored as **floating-point doubles rounded strictly to 2 decimal places** in MongoDB, validated to be non-negative ($\ge 0.00$).

---

## 💻 Installation & Local Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **MongoDB Server** (Running locally on port 27017 or a free cloud MongoDB Atlas cluster)

### 2. Verify MongoDB is Running
On Windows PowerShell:
```powershell
Get-Service -Name MongoDB
```
If not running, start it:
```powershell
net start MongoDB
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default contents of `.env`:
```ini
MONGO_URI=mongodb://localhost:27017/
DATABASE_NAME=rideshare_delivery_db
TEST_DATABASE_NAME=rideshare_delivery_test_db
APP_PORT=8501
APP_HOST=localhost
DEBUG=False
```
*(If using MongoDB Atlas, replace `MONGO_URI` with your connection string: `mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`)*

### 4. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

---

## ⚡ Database Seeding & Reset

Populate the database with realistic synthetic data using the built-in seed CLI:

```powershell
# Fresh seed (drops previous data and applies validators + indexes)
python scripts/seed_data.py --reset

# Custom volume generation
python scripts/seed_data.py --users 50 --drivers 30 --restaurants 20 --rides 250 --orders 250
```

---

## 🚀 Launching the Web Dashboard

Start the Streamlit dashboard on your local machine:
```powershell
streamlit run app.py
```
Open your browser at: `http://localhost:8501`

---

## 🧪 Running Automated Tests

A dedicated test suite of **21 unit & integration tests** runs against an isolated database (`rideshare_delivery_test_db`), guaranteeing zero contamination of development data:

```powershell
python -m pytest -v
```

Expected Output:
```text
tests/test_aggregation.py::test_revenue_excludes_cancelled PASSED
tests/test_aggregation.py::test_status_breakdown PASSED
tests/test_aggregation.py::test_top_drivers_aggregation PASSED
tests/test_aggregation.py::test_revenue_by_cuisine_aggregation PASSED
tests/test_crud.py::test_user_crud PASSED
tests/test_crud.py::test_driver_crud PASSED
tests/test_crud.py::test_restaurant_crud PASSED
tests/test_crud.py::test_ride_crud PASSED
tests/test_crud.py::test_food_order_crud PASSED
tests/test_indexes.py::test_required_indexes_present PASSED
tests/test_indexes.py::test_create_and_drop_custom_index PASSED
tests/test_indexes.py::test_cannot_drop_primary_id_index PASSED
tests/test_indexes.py::test_explain_plan_analysis PASSED
tests/test_validation.py::test_invalid_email_format PASSED
tests/test_validation.py::test_duplicate_email_rejection PASSED
tests/test_validation.py::test_rating_bounds PASSED
tests/test_validation.py::test_positive_number_validation PASSED
tests/test_validation.py::test_invalid_object_id PASSED
tests/test_validation.py::test_foreign_key_missing_user_or_driver PASSED
tests/test_validation.py::test_invalid_ride_status PASSED
tests/test_validation.py::test_order_empty_items PASSED
============================== 21 passed in 0.66s ==============================
```

You can also run the full test suite live from inside the web dashboard under **"🛡️ Data Validation & Testing"**!

---

## 🌟 Core Feature Showcase

### 1. CRUD Operations & UI Management
- **Users**: Register users, search across name/email/phone, paginate, update profiles, and safely delete with checks preventing deletion if active rides/orders exist.
- **Drivers**: Onboard drivers, filter by vehicle type and availability, adjust ratings, track active rides.
- **Restaurants**: Partner eateries, filter by cuisine and minimum star rating, toggle operating status.
- **Rides**: Dispatch new trips with validated customer and driver dropdowns, route details, automated fare calculation, and status progression (`requested` ➡️ `accepted` ➡️ `in_progress` ➡️ `completed`).
- **Food Orders**: Dynamic subdocument item builder with automatic subtotal and delivery fee calculations, status progression (`placed` ➡️ `preparing` ➡️ `out_for_delivery` ➡️ `delivered`).

### 2. Advanced Query Demonstrations
- `$gt` / `$gte`: Identify high-value rides above a specified dollar threshold.
- Compound equality: Completed rides for a given driver (`driver_id` + `status: "completed"`).
- Date Range: Multi-day temporal queries (`created_at: {$gte: ..., $lte: ...}`).
- Cancellation Audits: Query cancelled rides and orders across both collections using `$in` / `$or`.
- Projections: Return lean subsets of document keys to optimize network bandwidth.

### 3. Aggregation Pipelines
- **Financial KPIs**: Sum platform revenue while strictly excluding cancelled orders:
  ```python
  pipeline = [
      {"$match": {"status": "completed"}},
      {"$group": {"_id": None, "total_revenue": {"$sum": "$fare"}, "avg_fare": {"$avg": "$fare"}}}
  ]
  ```
- **Revenue by Cuisine**: Joins orders with restaurants via `$lookup`, unwinds, groups by cuisine, and computes total earnings.
- **Parallel Facets (`$facet`)**: Aggregates ride volumes and food order volumes concurrently in a single database round-trip.

### 4. Data Validation (Dual-Layer)
1. **Database Level**: Applied via MongoDB `$jsonSchema` validators on collection creation/modification. Enforces types, regex email formats, enum statuses, and minimum item lengths directly inside the database engine.
2. **Application Level**: Validates inputs in Python before sending commands, preventing network overhead and providing user-friendly validation errors.

### 5. Index Management & Storage
- Unique index on `users.email` preventing duplicate customer accounts.
- Single-field indexes on `rides.driver_id`, `rides.status`, `rides.created_at`, `food_orders.restaurant_id`, `food_orders.status`.
- Compound indexes:
  - `idx_rides_driver_status`: `[("driver_id", 1), ("status", 1)]`
  - `idx_rides_status_created_at`: `[("status", 1), ("created_at", -1)]`
  - `idx_orders_restaurant_status`: `[("restaurant_id", 1), ("status", 1)]`
- Dynamic index builder & dropper directly in the web UI.

### 6. Query Optimization (`COLLSCAN` vs `IXSCAN`)
Provides live `explain("executionStats")` inspections:
- **`totalDocsExamined`**: Number of documents loaded into memory.
- **`totalKeysExamined`**: Number of B-Tree index keys traversed.
- **`executionTimeMillis`**: Server-side execution duration.
- **Winning Plan Stage**: Displays whether MongoDB used `COLLSCAN` (table scan) or `IXSCAN` (B-Tree index scan).

---

## 📊 Query Optimization Benchmark Results

We executed a controlled benchmark comparing unindexed versus indexed queries on a synthetic dataset of **5,000 documents** (`benchmark_rides`) querying `driver_code == "DRV-0042"`:

| Metric | Baseline (Without Index) | Optimized (With B-Tree Index) | Improvement |
| :--- | :--- | :--- | :--- |
| **Winning Plan Stage** | `COLLSCAN` (Full Table Scan) | `FETCH` + `IXSCAN` (Index Scan) | Algorithmic shift: $O(N) \to O(\log N)$ |
| **Documents Examined** | **5,000** | **24** | **99.52% Reduction** |
| **Keys Examined** | **0** | **24** | Targeted B-Tree traversal |
| **Documents Returned** | 24 | 24 | Identical dataset returned |
| **Server Latency** | 2 - 4 ms | 0 - 1 ms | $\approx 75\%$ latency reduction |

> [!NOTE]
> On tiny collections (< 100 documents), modern operating system RAM caches make timing differences negligible (0ms vs 0ms). The synthetic dataset generator in the **Query Performance** page allows demonstrating clear, tangible differences on realistic data volumes.

---

## ❓ Troubleshooting & Common Pitfalls

1. **MongoDB Connection Refused (`ServerSelectionTimeoutError`)**:
   - Ensure MongoDB service is running: Open PowerShell as Administrator and run `net start MongoDB`.
   - Verify port 27017 is open and accessible.
2. **Duplicate Key Error on Email**:
   - MongoDB enforces the unique index `idx_users_email_unique`. To register a user with a new profile, provide a distinct email address or reset the database via `python scripts/seed_data.py --reset`.
3. **Streamlit Port Already in Use**:
   - If port 8501 is occupied, launch on another port:
     ```powershell
     streamlit run app.py --server.port 8502
     ```

---

## 🎤 College Project Presentation Script

Use this step-by-step 5-minute presentation script when demonstrating this project to professors, evaluators, or interviewers:

### **Minute 1: Introduction & Architecture**
- *"Good morning/afternoon. Today I am presenting **Rideshare & Food Delivery Tracker**, a full-stack data engineering and logistics intelligence application built with Python, MongoDB, PyMongo, and Streamlit."*
- *"Rather than a toy single-table app, this models two interwoven on-demand verticals: ridesharing and multi-restaurant food delivery. It tracks customers, drivers, vehicles, restaurants, and financial transactions."*
- Show the **Dashboard Overview** page: point out the real-time KPI cards, revenue trends, status donut charts, and top-performing drivers.

### **Minute 2: Schema Validation & CRUD**
- *"To ensure high data integrity in a NoSQL environment, we implemented **dual-layer data validation**."*
- Navigate to **"Manage Users"** or **"Manage Rides"**:
- *"Notice that when creating a ride, foreign key references to `user_id` and `driver_id` are strictly validated, pickup and dropoff routes are checked, and fares are calculated."*
- Navigate to **"🛡️ Data Validation & Testing"**:
- Show the interactive sandbox: trigger the duplicate email test and the negative fare test to show how MongoDB and Python gracefully reject invalid states.

### **Minute 3: Advanced MongoDB Queries**
- Navigate to **"⚡ Advanced Queries"**:
- *"MongoDB provides rich query operators beyond simple lookups. Here, we can filter rides with fares above a threshold using `$gt`, locate completed trips for a specific driver with compound queries, and audit system cancellations across multiple collections."*
- Run query scenario #1 or #2 and show the embedded PyMongo code snippet.

### **Minute 4: Aggregation Pipelines**
- Navigate to **"🧠 Aggregation Analytics"**:
- *"For business intelligence, we leverage multi-stage MongoDB aggregation pipelines."*
- Explain: *"To calculate accurate gross platform revenue, we must strictly exclude cancelled orders. We do this via `$match: {status: 'completed'}` followed by `$group`. We also use `$lookup` and `$unwind` to join food orders with restaurants to calculate revenue by cuisine, and `$facet` to process ride and food order trends in parallel."*

### **Minute 5: Query Optimization & Live Test Suite**
- Navigate to **"⚡ Query Performance"**:
- *"Finally, let's examine database optimization. Under the hood, MongoDB uses query planner heuristics."*
- Run the **Before & After Index Benchmark**:
- Show how an unindexed query performs a `COLLSCAN` examining all 5,000 documents, whereas adding an index switches the engine to an `IXSCAN`, slashing document examinations by over **99%**.
- Conclude by running the **Live Pytest Suite** under Data Validation to show that all 21 automated tests pass.
>>>>>>> 31c85c7 (feat: complete Indian Rideshare & Food Delivery Tracker with premium UI and verified MongoDB CRUD)
