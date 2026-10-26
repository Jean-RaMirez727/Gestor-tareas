from datetime import date, timedelta

from gestor.core import Priority, Task
from gestor.queries import DueStatus, all_of, apply_filters, by_status, categories_of, due_status, sort_tasks, summarize

TODAY = date(2026, 10, 25)


def make(id_, priority=Priority.MEDIA, category="General", due=None, done=False):
    return Task(id_, "t", priority, category, due, None, done)


def test_filters_compose():
    tasks = (make(1, priority=Priority.ALTA), make(2, done=True), make(3, category="Uni"))
    assert [t.id for t in apply_filters(tasks, "pendientes", "todas", "todas")] == [1, 3]
    assert [t.id for t in apply_filters(tasks, "todas", "alta", "todas")] == [1]
    assert [t.id for t in apply_filters(tasks, "pendientes", "todas", "Uni")] == [3]


def test_all_of_is_a_closure_over_predicates():
    predicate = all_of(by_status("pendientes"), lambda t: t.category == "Uni")
    assert predicate(make(1, category="Uni")) and not predicate(make(2, done=True, category="Uni"))


def test_due_status_and_summary():
    tasks = (
        make(1, due=TODAY - timedelta(days=1)), make(2, due=TODAY), make(3, due=TODAY + timedelta(days=2)),
        make(4), make(5, done=True),
    )
    assert [due_status(t, TODAY) for t in tasks] == [
        DueStatus.OVERDUE, DueStatus.TODAY, DueStatus.ON_TIME, DueStatus.NO_DATE, DueStatus.COMPLETED]
    s = summarize(tasks, TODAY)
    assert (s.total, s.pending, s.completed, s.overdue) == (5, 4, 1, 1)


def test_sort_orders_pending_by_priority_then_date():
    tasks = (make(1, priority=Priority.BAJA), make(2, priority=Priority.ALTA, due=TODAY), make(3, done=True, priority=Priority.ALTA))
    assert [t.id for t in sort_tasks(tasks)] == [2, 1, 3]


def test_sort_accepts_custom_key():
    tasks = (make(1, category="B"), make(2, category="A"))
    assert [t.id for t in sort_tasks(tasks, key=lambda t: (t.category,))] == [2, 1]


def test_categories_are_unique_and_sorted():
    assert categories_of((make(1, category="B"), make(2, category="A"), make(3, category="B"))) == ("A", "B")
