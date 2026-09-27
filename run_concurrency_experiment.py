import os
import sqlite3
import threading
import time

DB_PATH = "concurrency_experiment.db"


def setup_experiment_db() -> None:
    """Creates a fresh, isolated database for the concurrency experiment."""
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE tickets (
            ticket_id INTEGER PRIMARY KEY,
            reopen_count INTEGER NOT NULL DEFAULT 0
        );
    """
    )
    cursor.execute("INSERT INTO tickets (ticket_id, reopen_count) VALUES (1, 0);")
    conn.commit()
    conn.close()


def reopen_ticket_naive(conn: sqlite3.Connection, ticket_id: int) -> None:
    """
    Naive read-modify-write without an explicit transaction (autocommit per statement).
    Vulnerable to lost-update anomaly when concurrent threads interleave.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT reopen_count FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    current_count = row[0] if row else 0

    # Introduce brief delay to ensure thread interleaving during read-modify-write window
    time.sleep(0.02)

    cursor.execute(
        "UPDATE tickets SET reopen_count = ? WHERE ticket_id = ?",
        (current_count + 1, ticket_id)
    )
    conn.commit()


def reopen_ticket_safe(conn: sqlite3.Connection, ticket_id: int) -> None:
    """
    Safe read-modify-write wrapped inside a BEGIN IMMEDIATE transaction.
    Acquires a reserved lock immediately, serializing concurrent writes and preventing lost updates.
    """
    cursor = conn.cursor()
    # Retry loop to handle SQLITE_BUSY / locks when acquiring BEGIN IMMEDIATE lock
    while True:
        try:
            cursor.execute("BEGIN IMMEDIATE")
            break
        except sqlite3.OperationalError:
            time.sleep(0.005)

    try:
        cursor.execute("SELECT reopen_count FROM tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        current_count = row[0] if row else 0

        time.sleep(0.02)

        cursor.execute(
            "UPDATE tickets SET reopen_count = ? WHERE ticket_id = ?",
            (current_count + 1, ticket_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def worker_naive(barrier: threading.Barrier, ticket_id: int) -> None:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    barrier.wait()
    reopen_ticket_naive(conn, ticket_id)
    conn.close()


def worker_safe(barrier: threading.Barrier, ticket_id: int) -> None:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    barrier.wait()
    reopen_ticket_safe(conn, ticket_id)
    conn.close()


def run_experiment():
    print("==================================================")
    print("SentinelDesk Concurrency Experiment (Task 3)")
    print("==================================================")

    # 1. Naive Trials
    print("\n--- Running 5 Trials of reopen_ticket_naive ---")
    naive_results = []
    for trial in range(1, 6):
        setup_experiment_db()
        barrier = threading.Barrier(2)

        t1 = threading.Thread(target=worker_naive, args=(barrier, 1))
        t2 = threading.Thread(target=worker_naive, args=(barrier, 1))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        conn = sqlite3.connect(DB_PATH)
        final_val = conn.execute(
            "SELECT reopen_count FROM tickets WHERE ticket_id = 1"
        ).fetchone()[0]
        conn.close()
        naive_results.append(final_val)
        print(f"Naive Trial {trial}: final reopen_count = {final_val}")

    # 2. Safe Trials
    print("\n--- Running 5 Trials of reopen_ticket_safe ---")
    safe_results = []
    for trial in range(1, 6):
        setup_experiment_db()
        barrier = threading.Barrier(2)

        t1 = threading.Thread(target=worker_safe, args=(barrier, 1))
        t2 = threading.Thread(target=worker_safe, args=(barrier, 1))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        conn = sqlite3.connect(DB_PATH)
        final_val = conn.execute(
            "SELECT reopen_count FROM tickets WHERE ticket_id = 1"
        ).fetchone()[0]
        conn.close()
        safe_results.append(final_val)
        print(f"Safe Trial {trial}: final reopen_count = {final_val}")

    print("\n--------------------------------------------------")
    print(f"Summary Naive Final Values: {naive_results}")
    print(f"Summary Safe Final Values:  {safe_results}")
    print("--------------------------------------------------")

    # Cleanup temp db
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass


if __name__ == "__main__":
    run_experiment()
