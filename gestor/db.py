"""IMPERATIVE SHELL - persistencia. Aquí viven los efectos de SQLite."""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date

from .core import Task, option_map, task_from_row
from .decorators import catching, logged

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT    NOT NULL,
    priority  TEXT    NOT NULL CHECK (priority IN ('alta', 'media', 'baja')),
    category  TEXT    NOT NULL,
    due_date  TEXT,
    notes     TEXT,
    completed INTEGER NOT NULL DEFAULT 0
)
"""


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(os.environ.get("GESTOR_DB", "tareas.db"))


@catching(sqlite3.Error, message="No se pudo inicializar la base de datos")
@logged
def init_db() -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(SCHEMA)


@catching(sqlite3.Error, message="No se pudo guardar la tarea")
@logged
def insert_task(task: Task) -> Task:
    with closing(_connect()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, priority, category, due_date, notes, completed) VALUES (?, ?, ?, ?, ?, ?)",
            (
                task.title,
                task.priority.value,
                task.category,
                option_map(task.due_date, date.isoformat),
                task.notes,
                int(task.completed),
            ),
        )
        return replace(task, id=cursor.lastrowid)


@catching(sqlite3.Error, message="No se pudieron leer las tareas")
@logged
def list_tasks() -> tuple[Task, ...]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, title, priority, category, due_date, notes, completed FROM tasks ORDER BY id"
        ).fetchall()
    return tuple(map(task_from_row, rows))


@catching(sqlite3.Error, LookupError, message="No se pudo actualizar la tarea")
@logged
def set_completed(task_id: int, completed: bool) -> None:
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(completed), task_id))
        if cursor.rowcount == 0:
            raise LookupError(f"la tarea {task_id} ya no existe")


@catching(sqlite3.Error, LookupError, message="No se pudo eliminar la tarea")
@logged
def delete_task(task_id: int) -> None:
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise LookupError(f"la tarea {task_id} ya no existe")
