"""Garantiza la regla central de la arquitectura: el Functional Core no hace efectos."""
import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent / "gestor"
PURE_MODULES = ("core.py", "queries.py")
FORBIDDEN_IMPORTS = {"sqlite3", "reactpy", "fastapi", "os", "sys", "logging", "time", "random", "pathlib", "gestor.db", "gestor.ui"}
FORBIDDEN_CALLS = (".today(", ".now(", "print(", "open(")


def imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
            names.update(f".{alias.name}" for alias in node.names if node.level)
    return names


@pytest.mark.parametrize("module", PURE_MODULES)
def test_pure_modules_have_no_effectful_imports(module):
    path = ROOT / module
    if not path.exists():
        pytest.skip(f"{module} aún no está integrado en esta rama")
    names = imported_names(ast.parse(path.read_text()))
    assert not (names & FORBIDDEN_IMPORTS), f"{module} importa módulos con efectos: {names & FORBIDDEN_IMPORTS}"
    assert not ({".db", ".ui", ".decorators"} & names), f"{module} no debe depender del shell"


@pytest.mark.parametrize("module", PURE_MODULES)
def test_pure_modules_do_not_read_clock_or_do_io(module):
    path = ROOT / module
    if not path.exists():
        pytest.skip(f"{module} aún no está integrado en esta rama")
    source = path.read_text()
    assert not [call for call in FORBIDDEN_CALLS if call in source]
