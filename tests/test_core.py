from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from gestor.core import (
    Err, Ok, Priority, Task, bind, build_task, map_result, option_map, option_or,
    remove_task, replace_task, toggle_completed,
)


def make(id_, title="t", priority=Priority.MEDIA, category="General", due=None, done=False):
    return Task(id_, title, priority, category, due, None, done)


def test_build_task_ok():
    match build_task({"title": "  Estudiar  ", "priority": "alta", "due_date": "2026-11-01", "notes": " ", "category": ""}):
        case Ok(task):
            assert task.title == "Estudiar" and task.priority is Priority.ALTA
            assert task.due_date == date(2026, 11, 1) and task.notes is None and task.category == "General"
        case Err(error):
            pytest.fail(error)


@pytest.mark.parametrize("form", [
    {"title": "", "priority": "alta"},
    {"title": "x", "priority": "urgente"},
    {"title": "x", "priority": "alta", "due_date": "31/12/2026"},
    {"title": "x" * 81, "priority": "alta"},
])
def test_build_task_errors(form):
    assert isinstance(build_task(form), Err)


def test_bind_and_map_result_short_circuit_on_err():
    boom = Err("falló")
    assert bind(boom, lambda v: Ok(v + 1)) is boom
    assert map_result(Ok(1), lambda v: v + 1) == Ok(2)


def test_immutability():
    task = make(1)
    with pytest.raises(FrozenInstanceError):
        task.title = "otro"
    done = toggle_completed(task)
    assert done.completed and not task.completed


def test_collection_ops_do_not_mutate():
    original = (make(1), make(2))
    assert len(remove_task(original, 1)) == 1 and len(original) == 2
    assert replace_task(original, toggle_completed(original[0]))[0].completed and not original[0].completed


def test_option_helpers():
    assert option_map(None, str.upper) is None and option_map("a", str.upper) == "A"
    assert option_or(None, 5) == 5 and option_or(3, 5) == 3
