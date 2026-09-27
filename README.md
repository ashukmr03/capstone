# SentinelDesk — IT Asset & Ticket Management Platform

SentinelDesk is a lightweight, high-performance IT Asset and Ticket Management system engineered for Zoho's Bengaluru office. It replaces ad-hoc spreadsheet tracking with an object-oriented Python domain model, an SQLite-backed persistence and transactional audit layer, analytical reporting queries, lock-based concurrency controls, and high-level architectural documentation.

---

## 📁 Repository Structure

```text
sentineldesk/
├── README.md                  # Project setup, execution guide, and empirical test results
├── engine.py                  # Part 1 — Domain model hierarchy (Ticket, Asset, Employee) + HelpdeskEngine
├── schema.sql                 # Part 2 Task 1 — DDL Schema (3NF normalized)
├── seed_data.sql              # Part 2 Task 1 — Verbatim INSERT seed data (12 employees, 18 assets, 30 tickets, 50 history rows)
├── repository.py              # Part 2 Task 2 — Transactional write path (update_ticket_status with ROLLBACK on error)
├── run_concurrency_experiment.py # Part 2 Task 3 — Multithreaded lost-update anomaly vs. BEGIN IMMEDIATE concurrency experiment
├── reports/                   # Part 2 Task 4 — Analytical SQL reports
│   ├── report_tickets_per_employee_inner.sql
│   ├── report_tickets_per_employee_left.sql
│   ├── report_asset_ticket_coverage.sql
│   ├── report_employees_above_average.sql
│   ├── report_asset_type_overlap.sql
│   ├── report_type_status_having.sql
│   └── report_employee_rank_window.sql
├── INDEXING_NOTES.md          # Part 2 Task 5 — EXPLAIN QUERY PLAN analysis before/after composite index creation
└── DESIGN.md                  # Part 3 — HLD, LLD (SOLID justifications), UML diagrams, and Scale-Readiness roadmap
```

---

## 🚀 Setup & Execution Guide

### Prerequisites
* Python 3.10+ (Uses standard library modules `sqlite3`, `abc`, `datetime`, `threading`). No third-party packages or server installations required.

### 1. Initialize Database & Run Seed Data
```bash
python -c "import sqlite3; conn = sqlite3.connect('sentineldesk.db'); conn.executescript(open('schema.sql').read()); conn.executescript(open('seed_data.sql').read()); print('Database initialized successfully.'); conn.close()"
```

### 2. Verify Part 1 In-Memory Engine & Domain Model
```bash
python -c "import engine; eng = engine.HelpdeskEngine(); eng.load_from_db('sentineldesk.db'); print('Employees loaded:', len(eng.employees_by_id)); print('Assets loaded:', len(eng.assets_by_id)); print('Open tickets:', len(eng.tickets_by_status['Open'])); print('Ticket types seen:', eng.ticket_type_seen)"
```

### 3. Verify Part 2 Task 2 Transactional Atomicity
```bash
python -c "import sqlite3, repository; conn = sqlite3.connect('sentineldesk.db'); repo = repository.Repository(); status_before = conn.execute('SELECT status FROM tickets WHERE ticket_id=1').fetchone()[0]; print('Status before invalid update:', status_before); try: repo.update_ticket_status(conn, 1, 'Cancelled')\nexcept Exception as e: print('Caught error as expected:', e); status_after = conn.execute('SELECT status FROM tickets WHERE ticket_id=1').fetchone()[0]; print('Status after failed update:', status_after); assert status_before == status_after; print('Atomicity verified!')"
```

### 4. Run Part 2 Task 3 Concurrency Experiment
```bash
python run_concurrency_experiment.py
```

---

## 🧪 Part 2 Task 2 — Transactional Atomicity Test Output

When attempting a status update with an invalid status `'Cancelled'` (which violates the `CHECK` constraint `status IN ('Open','InProgress','Resolved','Closed')`), the transaction is rolled back completely:

```text
Before invalid update: status = 'Closed', history_rows = 50
IntegrityError caught: CHECK constraint failed: status IN ('Open','InProgress','Resolved','Closed')
After failed update:   status = 'Closed', history_rows = 50
[SUCCESS] Zero rows changed in tickets or ticket_status_history.
```

---

## 🔒 Part 2 Task 3 — Concurrency Experiment & Theoretical Explanation

### Terminal Output
Pasted verbatim output from running `run_concurrency_experiment.py`:

```text
==================================================
SentinelDesk Concurrency Experiment (Task 3)
==================================================

--- Running 5 Trials of reopen_ticket_naive ---
Naive Trial 1: final reopen_count = 1
Naive Trial 2: final reopen_count = 1
Naive Trial 3: final reopen_count = 1
Naive Trial 4: final reopen_count = 1
Naive Trial 5: final reopen_count = 1

--- Running 5 Trials of reopen_ticket_safe ---
Safe Trial 1: final reopen_count = 2
Safe Trial 2: final reopen_count = 2
Safe Trial 3: final reopen_count = 2
Safe Trial 4: final reopen_count = 2
Safe Trial 5: final reopen_count = 2

--------------------------------------------------
Summary Naive Final Values: [1, 1, 1, 1, 1]
Summary Safe Final Values:  [2, 2, 2, 2, 2]
--------------------------------------------------
```

### Lock-Based Concurrency Control Explanation
The concurrency experiment uses **lock-based concurrency control**. In the naive version (`reopen_ticket_naive`), autocommit per statement allows both concurrent threads to read `reopen_count = 0` simultaneously before either thread writes back `0 + 1`, causing a lost update anomaly where the final increment is `1` instead of `2`. Wrapping the read-modify-write block in `BEGIN IMMEDIATE` (`reopen_ticket_safe`) fixes this because `BEGIN IMMEDIATE` instructs SQLite to acquire a reserved write lock on the database file *before* executing the read query. This forces the second thread to wait until the first thread completes its update and commits its transaction, enforcing serial execution and guaranteeing the correct final value of `2` across all 5 trials.

---

## 📊 Part 2 Task 4 — Analytical SQL Report Outputs

All report queries were executed against `sentineldesk.db` populated with the exact seed data from Task 1.

### Report A: `reports/report_tickets_per_employee_inner.sql`
* **Goal**: INNER JOIN employees and tickets on `raised_by`, grouped by employee.
* **Output** (11 rows; Priya Das, `emp_id = 12`, raised 0 tickets and is excluded):

```text
(1, 'Aarav Sharma', 'Engineering', 7)
(2, 'Isha Verma', 'IT Support', 1)
(3, 'Rohan Gupta', 'Design', 1)
(4, 'Diya Nair', 'Sales', 1)
(5, 'Kabir Singh', 'HR', 1)
(6, 'Meera Iyer', 'Engineering', 2)
(7, 'Vivaan Rao', 'IT Support', 4)
(8, 'Ananya Joshi', 'Design', 1)
(9, 'Aditya Menon', 'Sales', 3)
(10, 'Sara Khan', 'HR', 2)
(11, 'Arjun Reddy', 'Engineering', 7)
```

### Report B: `reports/report_tickets_per_employee_left.sql`
* **Goal**: LEFT JOIN employees and tickets, comparing `COUNT(*)` vs `COUNT(t.ticket_id)`.
* **Output** (All 12 employees returned):

```text
(1, 'Aarav Sharma', 'Engineering', 7, 7)
(2, 'Isha Verma', 'IT Support', 1, 1)
(3, 'Rohan Gupta', 'Design', 1, 1)
(4, 'Diya Nair', 'Sales', 1, 1)
(5, 'Kabir Singh', 'HR', 1, 1)
(6, 'Meera Iyer', 'Engineering', 2, 2)
(7, 'Vivaan Rao', 'IT Support', 4, 4)
(8, 'Ananya Joshi', 'Design', 1, 1)
(9, 'Aditya Menon', 'Sales', 3, 3)
(10, 'Sara Khan', 'HR', 2, 2)
(11, 'Arjun Reddy', 'Engineering', 7, 7)
(12, 'Priya Das', 'IT Support', 1, 0)
```
* **Explanation**: For Priya Das (`emp_id = 12`), `COUNT(*)` returns `1` because it counts the single NULL-padded joined row produced by the LEFT JOIN, whereas `COUNT(t.ticket_id)` returns `0` because it evaluates only non-NULL `ticket_id` values.

### Report C: `reports/report_asset_ticket_coverage.sql`
* **Goal**: LEFT JOIN assets and tickets on `asset_id`, plus independent `NOT IN` confirmation.
* **Query 1 Output** (All 18 assets; AST-018 has 0 tickets):

```text
(1, 'AST-001', 'Laptop', 2)
(2, 'AST-002', 'Monitor', 4)
(3, 'AST-003', 'Server', 1)
(4, 'AST-004', 'Networking', 1)
(5, 'AST-005', 'Printer', 2)
(6, 'AST-006', 'Laptop', 3)
(7, 'AST-007', 'Monitor', 0)
(8, 'AST-008', 'Server', 2)
(9, 'AST-009', 'Networking', 0)
(10, 'AST-010', 'Printer', 1)
(11, 'AST-011', 'Laptop', 2)
(12, 'AST-012', 'Monitor', 1)
(13, 'AST-013', 'Server', 0)
(14, 'AST-014', 'Networking', 0)
(15, 'AST-015', 'Printer', 0)
(16, 'AST-016', 'Laptop', 0)
(17, 'AST-017', 'Monitor', 1)
(18, 'AST-018', 'Server', 0)
```

* **Query 2 Output** (Independent `NOT IN` confirmation of assets with 0 tickets):

```text
(7, 'AST-007', 'Monitor')
(9, 'AST-009', 'Networking')
(13, 'AST-013', 'Server')
(14, 'AST-014', 'Networking')
(15, 'AST-015', 'Printer')
(16, 'AST-016', 'Laptop')
(18, 'AST-018', 'Server')
```

### Report D: `reports/report_employees_above_average.sql`
* **Goal**: List employees whose ticket count exceeds average tickets per raiser (30 / 11 ≈ 2.727).
* **Output** (Exactly 4 employees):

```text
(1, 'Aarav Sharma', 7)
(11, 'Arjun Reddy', 7)
(7, 'Vivaan Rao', 4)
(9, 'Aditya Menon', 3)
```

### Report E: `reports/report_asset_type_overlap.sql`
* **Goal**: Set operations (UNION and EXCEPT) on assets linked to `incident` and `maintenance` tickets.
* **(i) UNION Output** (8 distinct asset IDs: `{1, 2, 3, 4, 5, 6, 8, 11}`):

```text
(1,)
(2,)
(3,)
(4,)
(5,)
(6,)
(8,)
(11,)
```

* **(ii) EXCEPT Output** (Incident minus Maintenance = 4 distinct asset IDs: `{3, 4, 8, 11}`):

```text
(3,)
(4,)
(8,)
(11,)
```

### Report F: `reports/report_type_status_having.sql`
* **Goal**: `GROUP BY (ticket_type, status)` HAVING `COUNT(*) >= 3`.
* **Output** (Exactly 5 rows):

```text
('incident', 'Open', 3)
('service_request', 'Closed', 4)
('service_request', 'InProgress', 3)
('service_request', 'Open', 7)
('service_request', 'Resolved', 4)
```

### Report G: `reports/report_employee_rank_window.sql`
* **Goal**: Window function `RANK() OVER (ORDER BY ticket_count DESC)` per raiser.
* **Output** (11 raisers; Aarav & Arjun tie at rank 1, Vivaan Rao skips to rank 3):

```text
(1, 'Aarav Sharma', 7, 1)
(11, 'Arjun Reddy', 7, 1)
(7, 'Vivaan Rao', 4, 3)
(9, 'Aditya Menon', 3, 4)
(6, 'Meera Iyer', 2, 5)
(10, 'Sara Khan', 2, 5)
(2, 'Isha Verma', 1, 7)
(3, 'Rohan Gupta', 1, 7)
(4, 'Diya Nair', 1, 7)
(5, 'Kabir Singh', 1, 7)
(8, 'Ananya Joshi', 1, 7)
```

---

## 📈 Part 2 Task 5 — Indexing Notes Summary

As documented in [`INDEXING_NOTES.md`](file:///c:/Users/User/OneDrive/Documents/capstone/INDEXING_NOTES.md), executing `EXPLAIN QUERY PLAN` on Report F before creating the composite index produces:

```text
SCAN tickets
USE TEMP B-TREE FOR GROUP BY
```

After executing `CREATE INDEX idx_tickets_type_status ON tickets(ticket_type, status);`, running `EXPLAIN QUERY PLAN` yields:

```text
SCAN tickets USING COVERING INDEX idx_tickets_type_status
```

The composite index stores pre-sorted tuples of `(ticket_type, status)`, enabling SQLite to fulfill the grouping and counting requirements directly from the index structure without spending CPU cycles creating a temporary B-tree.

---

## 🏛️ Part 3 — Design Architecture Summary

Refer to [`DESIGN.md`](file:///c:/Users/User/OneDrive/Documents/capstone/DESIGN.md) for the complete design document, featuring:
* **Layered HLD**: Mapping `HelpdeskEngine` (Business), `Repository` (Data Access), SQLite schema (Database), and CLI/Scripts (Presentation).
* **LLD & SOLID Principles**: Explicit justifications for `Ticket` (OCP), `IncidentTicket` (LSP), `HelpdeskEngine` (SRP), `Repository` (DIP), and `Asset` (ISP).
* **Mermaid Diagrams**: Domain Class Diagram and Transaction Status Sequence Diagram.
* **Scale-Readiness**: Bottleneck analysis, **Least Connection** load balancing with statelessness reasoning, and Microservices decomposition with soft-deletion reference integrity.
