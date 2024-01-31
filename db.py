from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Optional, Sequence

DATABASE = "todo.db"
SCHEMA = "schema.sql"


@dataclass
class Todo:
    ID: str = ""
    Title: str = ""
    Completed: bool = False
    OwnerID: str = ""

    @staticmethod
    def from_json(json_data: Any) -> Todo:
        return Todo(**json_data)


class Store:
    def __init__(self, db_file: str = DATABASE, schema_file: str = SCHEMA):
        self._db_file = db_file
        with self._conn as conn, open(schema_file) as f:
            conn.executescript(f.read())

    @property
    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_file)

    def list(self) -> Sequence[Todo]:
        with self._conn as conn:
            cur = conn.cursor().execute("SELECT * FROM todos")
            return [Todo(*row) for row in cur.fetchall()]

    def get(self, id: str) -> Todo:
        with self._conn as conn:
            cur = conn.cursor().execute("SELECT * FROM todos WHERE ID = ?", (id,))
            return Todo(*cur.fetchone())

    def insert(self, todo: Todo) -> None:
        with self._conn as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO todos (ID, Title, Completed, OwnerID) VALUES (?, ?, ?, ?)",
                (todo.ID, todo.Title, todo.Completed, todo.OwnerID),
            )
            conn.commit()

    def update(self, todo: Todo) -> None:
        with self._conn as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE todos SET Title = ?, Completed = ? WHERE ID = ?",
                (todo.Title, todo.Completed, todo.ID),
            )
            conn.commit()

    def delete(self, todo_id: str) -> None:
        with self._conn as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM todos WHERE ID = ?", (todo_id,))
            conn.commit()
