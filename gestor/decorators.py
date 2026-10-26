"""Decoradores del Imperative Shell: convierten y registran efectos secundarios."""
from __future__ import annotations

import functools
import logging
import time
from typing import Callable

from .core import Err, Ok

log = logging.getLogger("gestor")


def logged(fn: Callable) -> Callable:
    """Decorador simple: deja traza (efecto) de cada operación y su duración."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        log.info("%s ejecutada en %.1f ms", fn.__name__, (time.perf_counter() - start) * 1000)
        return result

    return wrapper


def catching(*exceptions: type[BaseException], message: str) -> Callable:
    """Decorador con argumentos (fábrica + closure).

    Transforma una función impura que puede lanzar excepciones en una que
    devuelve Result: Ok(valor) o Err(mensaje). Así el shell maneja errores
    como datos, sin try/except dispersos en la interfaz.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return Ok(fn(*args, **kwargs))
            except exceptions as exc:
                log.error("%s falló: %s", fn.__name__, exc)
                return Err(f"{message}: {exc}")

        return wrapper

    return decorator
