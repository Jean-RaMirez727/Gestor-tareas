"""FUNCTIONAL CORE
================
Modelo, validación y transformaciones puras del dominio. Este módulo NO realiza entrada/salida:
no toca SQLite, no lee el reloj del sistema, no imprime, no muta estructuras.
Todo lo que necesita (por ejemplo, la fecha actual) llega como argumento.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import Callable, Generic, Mapping, TypeVar

T = TypeVar("T")
U = TypeVar("U")


# --------------------------------------------------------------------------- #
# Modelo inmutable
# --------------------------------------------------------------------------- #
class Priority(Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


PRIORITY_BY_VALUE: Mapping[str, Priority] = {p.value: p for p in Priority}


@dataclass(frozen=True, slots=True)
class Task:
    """Tarea inmutable. `id`, `due_date` y `notes` pueden estar AUSENTES (None)."""

    id: int | None
    title: str
    priority: Priority
    category: str
    due_date: date | None
    notes: str | None
    completed: bool = False


# --------------------------------------------------------------------------- #
# Manejo funcional de errores: Result = Ok | Err (sin excepciones en el dominio)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Err:
    error: str


Result = Ok | Err


def map_result(result: Result, fn: Callable[[T], U]) -> Result:
    """Aplica `fn` solo si hay éxito (orden superior)."""
    match result:
        case Ok(value):
            return Ok(fn(value))
        case Err():
            return result


def bind(result: Result, fn: Callable[[T], Result]) -> Result:
    """Encadena operaciones que pueden fallar; el primer Err corta la cadena."""
    match result:
        case Ok(value):
            return fn(value)
        case Err():
            return result


# --------------------------------------------------------------------------- #
# Ausencia de valor: ayudantes sobre None (alternativa a if/else dispersos)
# --------------------------------------------------------------------------- #
def option_map(value: T | None, fn: Callable[[T], U]) -> U | None:
    return None if value is None else fn(value)


def option_or(value: T | None, default: T) -> T:
    return default if value is None else value


# --------------------------------------------------------------------------- #
# Validación (cada regla es una función pura que devuelve Result)
# --------------------------------------------------------------------------- #
MAX_TITLE = 80
MAX_CATEGORY = 30
DEFAULT_CATEGORY = "General"


def validate_title(raw: str | None) -> Result:
    match (raw or "").strip():
        case "":
            return Err("El título es obligatorio.")
        case title if len(title) > MAX_TITLE:
            return Err(f"El título no puede superar {MAX_TITLE} caracteres.")
        case title:
            return Ok(title)


def parse_priority(raw: str | None) -> Result:
    match PRIORITY_BY_VALUE.get((raw or "").strip().lower()):
        case None:
            return Err("La prioridad debe ser alta, media o baja.")
        case priority:
            return Ok(priority)


def parse_due_date(raw: str | None) -> Result:
    match (raw or "").strip():
        case "":
            return Ok(None)  # la fecha límite es opcional
        case text:
            try:
                return Ok(date.fromisoformat(text))
            except ValueError:
                return Err("La fecha límite no tiene un formato válido (AAAA-MM-DD).")


def normalize_category(raw: str | None) -> str:
    return option_or((raw or "").strip()[:MAX_CATEGORY] or None, DEFAULT_CATEGORY)


def normalize_notes(raw: str | None) -> str | None:
    return (raw or "").strip() or None


def build_task(form: Mapping[str, str]) -> Result:
    """Construye una Task nueva (sin id) a partir del formulario.

    Cada `lambda` anidada es un closure que captura los valores ya validados.
    """
    return bind(
        validate_title(form.get("title")),
        lambda title: bind(
            parse_priority(form.get("priority")),
            lambda priority: bind(
                parse_due_date(form.get("due_date")),
                lambda due: Ok(
                    Task(
                        id=None,
                        title=title,
                        priority=priority,
                        category=normalize_category(form.get("category")),
                        due_date=due,
                        notes=normalize_notes(form.get("notes")),
                    )
                ),
            ),
        ),
    )


# --------------------------------------------------------------------------- #
# Transformaciones inmutables: siempre devuelven valores nuevos
# --------------------------------------------------------------------------- #
def toggle_completed(task: Task) -> Task:
    return replace(task, completed=not task.completed)


def add_task(tasks: tuple[Task, ...], task: Task) -> tuple[Task, ...]:
    return (*tasks, task)


def replace_task(tasks: tuple[Task, ...], updated: Task) -> tuple[Task, ...]:
    return tuple(map(lambda t: updated if t.id == updated.id else t, tasks))


def remove_task(tasks: tuple[Task, ...], task_id: int) -> tuple[Task, ...]:
    return tuple(filter(lambda t: t.id != task_id, tasks))


def task_from_row(row: tuple) -> Task:
    """Traduce una fila de SQLite a un Task (pura: solo transforma datos)."""
    id_, title, priority, category, due, notes, completed = row
    return Task(
        id=id_,
        title=title,
        priority=Priority(priority),
        category=category,
        due_date=option_map(due, date.fromisoformat),
        notes=notes,
        completed=bool(completed),
    )
