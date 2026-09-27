# SentinelDesk Indexing Analysis (`INDEXING_NOTES.md`)

This document records the performance optimization of report query `report_type_status_having.sql` (Part 2 Task 4f) using SQLite's `EXPLAIN QUERY PLAN` before and after adding a composite index on the `tickets` table.

---

## 1. Target Query
```sql
SELECT 
    ticket_type, 
    status, 
    COUNT(*) AS ticket_count
FROM tickets
GROUP BY ticket_type, status
HAVING COUNT(*) >= 3;
```

---

## 2. Unindexed Query Execution Plan (Before Indexing)

Before creating the composite index, SQLite executes `EXPLAIN QUERY PLAN` as follows:

```text
QUERY PLAN
|--SCAN tickets
`--USE TEMP B-TREE FOR GROUP BY
```

### Plan Details:
1. `SCAN tickets`: SQLite performs a full table scan across all rows of the `tickets` table.
2. `USE TEMP B-TREE FOR GROUP BY`: Because table rows are unsorted by `(ticket_type, status)`, SQLite must dynamically build an in-memory temporary B-tree data structure to bucket rows and evaluate the `GROUP BY` clause.

---

## 3. Index Creation DDL

We create a composite index covering both columns referenced in the query's grouping clause:

```sql
CREATE INDEX idx_tickets_type_status ON tickets(ticket_type, status);
```

---

## 4. Indexed Query Execution Plan (After Indexing)

After creating `idx_tickets_type_status`, executing the identical `EXPLAIN QUERY PLAN` yields:

```text
QUERY PLAN
`--SCAN tickets USING COVERING INDEX idx_tickets_type_status
```

---

## 5. Summary Explanation

**Summary:** The composite index `idx_tickets_type_status` acts as a covering index that stores pre-sorted `(ticket_type, status)` tuples, allowing SQLite to satisfy the `GROUP BY` grouping and count aggregations directly from the index's pre-ordered structure without allocating a temporary B-tree.
