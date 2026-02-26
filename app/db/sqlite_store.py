"""
SQLite-backed employee store using Python's standard library `sqlite3`.

This replaces the in-memory store with a real DB while still respecting
the "no external dependencies" requirement.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import NamedTuple

from app.models.employee import Employee


class SearchFilters(NamedTuple):
    """Search criteria applied at DB layer."""

    org_id: str
    name: str | None = None
    department: str | None = None
    location: str | None = None
    position: str | None = None
    limit: int = 20
    offset: int = 0


DB_PATH = Path(__file__).resolve().parent / "employees.sqlite3"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    """Create table and seed data if needed."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT NOT NULL,
                location TEXT NOT NULL,
                position TEXT NOT NULL
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_emp_org ON employees(org_id)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_emp_org_dept "
            "ON employees(org_id, department)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_emp_org_loc "
            "ON employees(org_id, location)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_emp_org_pos "
            "ON employees(org_id, position)"
        )

        # Seed only once
        cur.execute("SELECT COUNT(*) AS c FROM employees")
        count = cur.fetchone()["c"]
        if count == 0:
            _seed_data(cur)

        conn.commit()
    finally:
        conn.close()


def _seed_data(cur: sqlite3.Cursor) -> None:
    seed = [
        ("e1", "org_a", "John Doe", "john@org-a.com", "Engineering", "HN", "SE"),
        ("e2", "org_a", "Jane Smith", "jane@org-a.com", "HR", "HCM", "Manager"),
        ("e3", "org_a", "Bob Johnson", "bob@org-a.com", "Engineering", "HN", "Lead"),
        ("e4", "org_a", "Alice Brown", "alice@org-a.com", "Finance", "DN", "Analyst"),
        ("e5", "org_b", "Charlie Wilson", "charlie@org-b.com", "Engineering", "HN", "Architect"),
        ("e6", "org_b", "Diana Prince", "diana@org-b.com", "Product", "HCM", "PM"),
        ("e7", "org_b", "John Smith", "john.s@org-b.com", "Engineering", "HN", "SE"),
    ]
    cur.executemany(
        """
        INSERT INTO employees (id, org_id, name, email, department, location, position)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        seed,
    )


class SQLiteEmployeeStore:
    """SQLite-backed store. Filters and pagination at DB layer."""

    def search(self, filters: SearchFilters) -> tuple[list[Employee], int]:
        conn = _get_connection()
        try:
            cur = conn.cursor()

            where_clauses = ["org_id = ?"]
            params: list[object] = [filters.org_id]

            if filters.name:
                where_clauses.append("LOWER(name) LIKE ?")
                params.append(f"%{filters.name.lower()}%")
            if filters.department:
                where_clauses.append("department = ?")
                params.append(filters.department)
            if filters.location:
                where_clauses.append("location = ?")
                params.append(filters.location)
            if filters.position:
                where_clauses.append("position = ?")
                params.append(filters.position)

            where_sql = " AND ".join(where_clauses)

            # Total count
            cur.execute(f"SELECT COUNT(*) AS c FROM employees WHERE {where_sql}", params)
            total = cur.fetchone()["c"]

            # Page data
            cur.execute(
                f"""
                SELECT id, org_id, name, email, department, location, position
                FROM employees
                WHERE {where_sql}
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                [*params, filters.limit, filters.offset],
            )
            rows = cur.fetchall()
            employees = [
                Employee(
                    id=row["id"],
                    org_id=row["org_id"],
                    name=row["name"],
                    email=row["email"],
                    department=row["department"],
                    location=row["location"],
                    position=row["position"],
                )
                for row in rows
            ]
            return employees, total
        finally:
            conn.close()


_initialized = False
_store: SQLiteEmployeeStore | None = None


def get_employee_store() -> SQLiteEmployeeStore:
    """Singleton store, ensures DB is initialized."""
    global _initialized, _store
    if not _initialized:
        _init_db()
        _initialized = True
    if _store is None:
        _store = SQLiteEmployeeStore()
    return _store

