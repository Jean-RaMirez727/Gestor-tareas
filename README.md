# Gestor de tareas y actividades

App en Python con **ReactPy** (UI), **FastAPI** (solo integra y sirve la app, sin API REST propia) y **SQLite**.
Arquitectura **Functional Core / Imperative Shell**.

## Ejecución

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn main:app --reload
```
Abrir http://127.0.0.1:8000 · Pruebas del núcleo: `python -m pytest -q`

> Se fija `reactpy==1.0.2` porque las versiones posteriores eliminaron `reactpy.backend.fastapi.configure`.

## Estructura

| Archivo | Capa | Responsabilidad |
|---|---|---|
| `gestor/core.py` | Functional Core | Modelo inmutable, `Result`, validación, transformaciones. Sin E/S |
| `gestor/queries.py` | Functional Core | Filtros, orden, estado de vencimiento y resumen. Sin E/S |
| `gestor/decorators.py` | Shell | `@logged` y `@catching(...)` (excepciones a `Result`) |
| `gestor/db.py` | Shell | Todas las operaciones SQLite |
| `gestor/ui.py` | Shell | Componente ReactPy, estado y manejadores de eventos |
| `main.py` | Shell | `FastAPI` + `configure(app, TaskApp)` |
| `tests/` | - | Pruebas del núcleo, de la persistencia, de los decoradores y de la arquitectura |

Reparto del trabajo en equipo: ver `docs/DIVISION_EQUIPO.md`.

## Evidencia por tema

| Tema | Dónde verlo |
|---|---|
| Funciones de orden superior | `queries.all_of`, `apply_filters` (`filter`), `summarize` (`reduce`), `sort_tasks(key=...)`; `core.replace_task` (`map`), `map_result`, `bind` |
| Lambdas | `queries.by_status`, `core.replace_task`, `core.build_task` (lambdas anidadas), `ui.field_updater` |
| Closures | `queries.by_priority` (captura `wanted`), `by_category`, `all_of`; `ui.make_toggle_handler`, `make_delete_handler`, `field_updater`; `decorators.catching` |
| Pattern matching | `core.validate_title`, `parse_priority`, `parse_due_date`; `queries.due_status` (tupla + guardas), `summarize`; `ui` (`match` sobre `Ok`/`Err`), `ui.due_badge` |
| Inmutabilidad | `Task`, `Summary`, `Ok`, `Err` son `frozen=True`; `toggle_completed` usa `replace`; el estado es una `tuple`; `EMPTY_FORM` es `MappingProxyType` |
| Pureza y efectos secundarios | `core.py` y `queries.py` no hacen E/S (lo verifica `tests/test_architecture.py`); `date.today()` se lee en `ui.TaskApp` y se inyecta; efectos aislados en `db.py` y `ui.py` |
| Ausencia de valor | `Task.due_date`/`notes`/`id` pueden ser `None`; `option_map`, `option_or`; `message=None` en la UI |
| Manejo funcional de errores | `Result = Ok | Err`, `bind`/`map_result`, `build_task` encadenado, `@catching` en la capa de datos |
| Decoradores | `@logged` (simple) y `@catching(sqlite3.Error, message=...)` (con argumentos) en `db.py` |

## Funciones

Crear (título, prioridad, categoría, fecha límite, notas), listar (ordenadas por pendiente, prioridad y fecha),
completar/reabrir, eliminar y filtrar por estado, prioridad y categoría. Tema oscuro.
