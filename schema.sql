-- SentinelDesk DDL Schema
-- Normal Form Justification:
-- This database schema satisfies Third Normal Form (3NF). Every table has a well-defined primary key, 
-- all non-key attributes are fully functionally dependent on the entire primary key (1NF/2NF), and 
-- there are no transitive dependencies between non-key attributes (3NF). For instance, in the 'employees' table, 
-- 'department' and 'role' describe the employee directly rather than determining each other; in 'tickets', 
-- foreign keys ('raised_by', 'asset_id') link directly to primary keys of referenced entities without redundant descriptive fields.

CREATE TABLE employees (
    emp_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY,
    asset_tag TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    assigned_to INTEGER REFERENCES employees(emp_id)
);

CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    raised_by INTEGER NOT NULL REFERENCES employees(emp_id),
    ticket_type TEXT NOT NULL CHECK (ticket_type IN ('incident','service_request','maintenance')),
    priority TEXT NOT NULL CHECK (priority IN ('Low','Medium','High','Critical')),
    status TEXT NOT NULL CHECK (status IN ('Open','InProgress','Resolved','Closed')),
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    reopen_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE ticket_status_history (
    history_id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TEXT NOT NULL
);
