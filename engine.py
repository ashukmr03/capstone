import abc
import datetime
import sqlite3
from typing import Optional, List, Dict, Set, Tuple


class Ticket(abc.ABC):
    """
    Abstract base class representing an IT ticket in SentinelDesk.
    Instantiating Ticket directly raises TypeError because resolution_checklist is an @abstractmethod.
    """
    def __init__(
        self,
        ticket_id: int,
        asset_id: Optional[int],
        raised_by: int,
        priority: str,
        status: str,
        created_at: str,
        resolved_at: Optional[str] = None,
        ticket_type: str = "",
        reopen_count: int = 0,
    ):
        self.ticket_id = ticket_id
        self.asset_id = asset_id
        self.raised_by = raised_by
        self.priority = priority
        self.status = status
        self.created_at = created_at
        self.resolved_at = resolved_at
        self.ticket_type = ticket_type
        self.reopen_count = reopen_count

    @abc.abstractmethod
    def resolution_checklist(self) -> List[str]:
        """Returns the specific resolution checklist steps for the ticket type."""
        pass

    def age_in_days(self, reference_date: str) -> int:
        """Computes the number of days between created_at and reference_date (YYYY-MM-DD)."""
        created = datetime.datetime.strptime(self.created_at, "%Y-%m-%d").date()
        ref = datetime.datetime.strptime(reference_date, "%Y-%m-%d").date()
        return (ref - created).days


class IncidentTicket(Ticket):
    """Ticket subclass representing system incidents or outages."""
    def resolution_checklist(self) -> List[str]:
        return [
            "Perform initial incident triage and impact assessment",
            "Identify root cause and isolate affected system component",
            "Apply fix or workaround and verify operational recovery",
            "Conduct post-incident review and update documentation",
        ]


class ServiceRequestTicket(Ticket):
    """Ticket subclass representing service or asset provisioning requests."""
    def resolution_checklist(self) -> List[str]:
        return [
            "Verify manager approval and entitlement authorization",
            "Provision requested software license or hardware asset",
            "Configure access permissions and notify requesting employee",
            "Obtain end-user confirmation and finalize request ticket",
        ]


class MaintenanceTicket(Ticket):
    """Ticket subclass representing scheduled system maintenance."""
    def resolution_checklist(self) -> List[str]:
        return [
            "Schedule maintenance downtime window and notify stakeholders",
            "Perform complete data backup and system configuration snapshot",
            "Execute planned hardware/software maintenance procedures",
            "Conduct post-maintenance health checks and restore service",
        ]


class Employee:
    """Represents an employee entity matching Part 2 schema."""
    def __init__(self, emp_id: int, name: str, department: str, role: str):
        self.emp_id = emp_id
        self.name = name
        self.department = department
        self.role = role


class Asset:
    """Represents an IT asset entity matching Part 2 schema."""
    def __init__(
        self,
        asset_id: int,
        asset_tag: str,
        category: str,
        purchase_date: str,
        assigned_to: Optional[int] = None,
    ):
        self.asset_id = asset_id
        self.asset_tag = asset_tag
        self.category = category
        self.purchase_date = purchase_date
        self.assigned_to = assigned_to


class HelpdeskEngine:
    """In-memory domain engine indexing employees, assets, and tickets."""
    def __init__(self):
        self.employees_by_id: Dict[int, Employee] = {}
        self.assets_by_id: Dict[int, Asset] = {}
        self.tickets_by_status: Dict[str, List[Ticket]] = {
            "Open": [],
            "InProgress": [],
            "Resolved": [],
            "Closed": [],
        }
        self.ticket_type_seen: Set[str] = set()
        self.count_by_type_status: Dict[Tuple[str, str], int] = {}

    def load_from_db(self, db_path: str) -> None:
        """Loads domain objects from SQLite database and populates in-memory indexes."""
        self.employees_by_id.clear()
        self.assets_by_id.clear()
        self.tickets_by_status = {"Open": [], "InProgress": [], "Resolved": [], "Closed": []}
        self.ticket_type_seen.clear()
        self.count_by_type_status.clear()

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Load Employees
        cursor.execute("SELECT emp_id, name, department, role FROM employees")
        for row in cursor.fetchall():
            emp = Employee(
                emp_id=row["emp_id"],
                name=row["name"],
                department=row["department"],
                role=row["role"],
            )
            self.employees_by_id[emp.emp_id] = emp

        # Load Assets
        cursor.execute("SELECT asset_id, asset_tag, category, purchase_date, assigned_to FROM assets")
        for row in cursor.fetchall():
            asset = Asset(
                asset_id=row["asset_id"],
                asset_tag=row["asset_tag"],
                category=row["category"],
                purchase_date=row["purchase_date"],
                assigned_to=row["assigned_to"],
            )
            self.assets_by_id[asset.asset_id] = asset

        # Load Tickets
        cursor.execute(
            "SELECT ticket_id, asset_id, raised_by, ticket_type, priority, status, created_at, resolved_at, reopen_count FROM tickets"
        )
        for row in cursor.fetchall():
            t_type = row["ticket_type"]
            t_status = row["status"]

            # Factory instantiation based on ticket_type
            if t_type == "incident":
                ticket = IncidentTicket(
                    ticket_id=row["ticket_id"],
                    asset_id=row["asset_id"],
                    raised_by=row["raised_by"],
                    priority=row["priority"],
                    status=t_status,
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    ticket_type=t_type,
                    reopen_count=row["reopen_count"],
                )
            elif t_type == "service_request":
                ticket = ServiceRequestTicket(
                    ticket_id=row["ticket_id"],
                    asset_id=row["asset_id"],
                    raised_by=row["raised_by"],
                    priority=row["priority"],
                    status=t_status,
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    ticket_type=t_type,
                    reopen_count=row["reopen_count"],
                )
            elif t_type == "maintenance":
                ticket = MaintenanceTicket(
                    ticket_id=row["ticket_id"],
                    asset_id=row["asset_id"],
                    raised_by=row["raised_by"],
                    priority=row["priority"],
                    status=t_status,
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    ticket_type=t_type,
                    reopen_count=row["reopen_count"],
                )
            else:
                raise ValueError(f"Unknown ticket_type encountered in DB: {t_type}")

            # Indexing
            if t_status not in self.tickets_by_status:
                self.tickets_by_status[t_status] = []
            self.tickets_by_status[t_status].append(ticket)

            self.ticket_type_seen.add(t_type)

            pair = (t_type, t_status)
            self.count_by_type_status[pair] = self.count_by_type_status.get(pair, 0) + 1

        conn.close()


def notify(ticket: Ticket) -> List[str]:
    """
    Executes the resolution checklist notification for a given Ticket object.
    
    Why this function is guaranteed to work:
    Because Ticket is an Abstract Base Class (inheriting from abc.ABC) with @abstractmethod resolution_checklist,
    Python prevents any subclass from being instantiated unless resolution_checklist is fully implemented.
    Therefore, any ticket object managed by the engine is statically guaranteed to possess the method.
    In contrast, under standard duck typing without ABC enforcement, an object missing resolution_checklist 
    would pass instantiation silently and only raise an AttributeError at runtime when notify() is invoked.
    """
    return ticket.resolution_checklist()
