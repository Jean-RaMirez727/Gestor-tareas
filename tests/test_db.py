import pytest

from gestor import db
from gestor.core import Err, Ok, Priority, Task


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("GESTOR_DB", str(tmp_path / "test.db"))
    assert isinstance(db.init_db(), Ok)


def new_task(title="Tarea"):
    return Task(None, title, Priority.ALTA, "Uni", None, "notas", False)


def test_insert_assigns_id_and_lists():
    match db.insert_task(new_task()):
        case Ok(task):
            assert task.id is not None
        case Err(error):
            pytest.fail(error)
    match db.list_tasks():
        case Ok(tasks):
            assert [t.title for t in tasks] == ["Tarea"] and tasks[0].notes == "notas"
        case Err(error):
            pytest.fail(error)


def test_set_completed_persists():
    task = db.insert_task(new_task()).value
    assert isinstance(db.set_completed(task.id, True), Ok)
    assert db.list_tasks().value[0].completed is True


def test_missing_task_returns_err_not_exception():
    assert isinstance(db.set_completed(999, True), Err)
    assert isinstance(db.delete_task(999), Err)


def test_delete_removes_task():
    task = db.insert_task(new_task()).value
    assert isinstance(db.delete_task(task.id), Ok)
    assert db.list_tasks().value == ()
