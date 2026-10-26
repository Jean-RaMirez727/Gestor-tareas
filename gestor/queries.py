"""FUNCTIONAL CORE - consultas
===========================
Filtros, orden, estado de vencimiento y resumen. Todo es puro: recibe datos
(incluida la fecha actual) y devuelve datos nuevos, sin efectos secundarios.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from functools import reduce
from typing import Callable, Iterable, Mapping

from .core import PRIORITY_BY_VALUE, Priority, Task, option_or

PRIORITY_WEIGHT: Mapping[Priority, int] = {Priority.ALTA: 0, Priority.MEDIA: 1, Priority.BAJA: 2}


class DueStatus(Enum):
    COMPLETED = "completada"
    NO_DATE = "sin fecha"
    OVERDUE = "vencida"
    TODAY = "vence hoy"
    ON_TIME = "en plazo"


# --------------------------------------------------------------------------- #
# Filtros: closures que devuelven predicados + composición de orden superior
# --------------------------------------------------------------------------- #
Predicate = Callable[[Task], bool]


def by_status(status: str) -> Predicate:
    match status:
        case "pendientes":
            return lambda t: not t.completed
        case "completadas":
            return lambda t: t.completed
        case _:
            return lambda t: True


def by_priority(value: str) -> Predicate:
    wanted = PRIORITY_BY_VALUE.get(value)  # capturado por el closure
    return (lambda t: True) if wanted is None else (lambda t: t.priority is wanted)


def by_category(category: str) -> Predicate:
    return (lambda t: True) if category in ("", "todas") else (lambda t: t.category == category)


def all_of(*predicates: Predicate) -> Predicate:
    return lambda task: all(predicate(task) for predicate in predicates)


def apply_filters(tasks: Iterable[Task], status: str, priority: str, category: str) -> tuple[Task, ...]:
    return tuple(filter(all_of(by_status(status), by_priority(priority), by_category(category)), tasks))


def sort_key(task: Task) -> tuple:
    """Pendientes primero, luego por prioridad y por fecha límite más cercana."""
    return (task.completed, PRIORITY_WEIGHT[task.priority], option_or(task.due_date, date.max))


def sort_tasks(tasks: Iterable[Task], key: Callable[[Task], tuple] = sort_key) -> tuple[Task, ...]:
    return tuple(sorted(tasks, key=key))


def categories_of(tasks: Iterable[Task]) -> tuple[str, ...]:
    return tuple(sorted({t.category for t in tasks}))


# --------------------------------------------------------------------------- #
# Estado de vencimiento y resumen (pattern matching + reduce)
# --------------------------------------------------------------------------- #
def due_status(task: Task, today: date) -> DueStatus:
    match (task.completed, task.due_date):
        case (True, _):
            return DueStatus.COMPLETED
        case (False, None):
            return DueStatus.NO_DATE
        case (False, due) if due < today:
            return DueStatus.OVERDUE
        case (False, due) if due == today:
            return DueStatus.TODAY
        case _:
            return DueStatus.ON_TIME


@dataclass(frozen=True, slots=True)
class Summary:
    total: int = 0
    pending: int = 0
    completed: int = 0
    overdue: int = 0


def summarize(tasks: Iterable[Task], today: date) -> Summary:
    def step(acc: Summary, task: Task) -> Summary:
        match due_status(task, today):
            case DueStatus.COMPLETED:
                return replace(acc, total=acc.total + 1, completed=acc.completed + 1)
            case DueStatus.OVERDUE:
                return replace(acc, total=acc.total + 1, pending=acc.pending + 1, overdue=acc.overdue + 1)
            case _:
                return replace(acc, total=acc.total + 1, pending=acc.pending + 1)

    return reduce(step, tasks, Summary())
