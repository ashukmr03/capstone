import datetime
import sqlite3
from typing import Optional


class Repository:
    """Data Access Repository layer managing transactional persistence for SentinelDesk."""

    def update_ticket_status(
        self, conn: sqlite3.Connection, ticket_id: int, new_status: str, changed_at: Optional[str] = None
    ) -> None:
        """
        Updates the status of a ticket and records the transition in ticket_status_history.
        Executed inside a single explicit transaction with mandatory ROLLBACK on failure (Atomicity).
        """
        if changed_at is None:
            changed_at = datetime.date.today().isoformat()

        cursor = conn.cursor()
        
        # Disable auto-commit implicit transaction to manage explicit transaction block
        # Or execute explicit BEGIN / COMMIT / ROLLBACK block
        try:
            cursor.execute("BEGIN TRANSACTION;")

            # 1. Query existing ticket status
            cursor.execute("SELECT status FROM tickets WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Ticket ID {ticket_id} not found.")
            old_status = row[0]

            # 2. Update status in tickets table (will raise sqlite3.IntegrityError if new_status violates CHECK)
            cursor.execute(
                "UPDATE tickets SET status = ? WHERE ticket_id = ?",
                (new_status, ticket_id)
            )

            # 3. Insert audit log into ticket_status_history
            cursor.execute(
                "INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_at) VALUES (?, ?, ?, ?)",
                (ticket_id, old_status, new_status, changed_at)
            )

            # Commit transaction on success
            conn.commit()
        except Exception as e:
            # Explicit rollback guarantees Atomicity
            conn.rollback()
            raise e
