import logging

from gestor.core import Err, Ok
from gestor.decorators import catching, logged


def test_catching_converts_exception_to_err():
    @catching(ValueError, message="fallo controlado")
    def risky():
        raise ValueError("boom")

    assert risky() == Err("fallo controlado: boom")


def test_catching_wraps_success_in_ok_and_preserves_name():
    @catching(ValueError, message="x")
    def fine(a, b):
        return a + b

    assert fine(1, 2) == Ok(3) and fine.__name__ == "fine"


def test_catching_does_not_swallow_other_exceptions():
    @catching(ValueError, message="x")
    def other():
        raise KeyError("k")

    try:
        other()
    except KeyError:
        return
    raise AssertionError("debió propagarse KeyError")


def test_logged_returns_value_and_emits_trace(caplog):
    @logged
    def work():
        return 42

    with caplog.at_level(logging.INFO, logger="gestor"):
        assert work() == 42
    assert any("work" in r.message for r in caplog.records)
