# División de responsabilidades (equipo de 3)

La app se parte por **capas de la arquitectura**, de modo que cada rama modifica archivos distintos y no se generan conflictos de fusión.

## 1. Ramas

| Rama | Responsable | Archivos que posee |
|---|---|---|
| `main` | Todos (solo por Pull Request) | Base: `README.md`, `requirements.txt`, `.gitignore`, `docs/`, `scripts/`, `__init__.py` |
| `develop` | Todos (integración) | Resultado de fusionar las tres ramas de trabajo |
| `feature/dominio-core` | **Integrante A** | `gestor/core.py`, `tests/test_core.py`, `tests/test_architecture.py` |
| `feature/persistencia-shell` | **Integrante B** | `gestor/decorators.py`, `gestor/db.py`, `main.py`, `tests/test_db.py`, `tests/test_decorators.py` |
| `feature/consultas-ui` | **Integrante C** | `gestor/queries.py`, `gestor/ui.py`, `tests/test_queries.py` |

**Regla de propiedad:** solo el dueño de un archivo lo modifica. Si otro integrante necesita un cambio, lo solicita por *issue* o lo propone en la revisión del PR.

## 2. Responsabilidades y temas obligatorios

| | Integrante A: Dominio puro | Integrante B: Shell de datos | Integrante C: Consultas e interfaz |
|---|---|---|---|
| Responde por | Modelo, validación, `Result`, transformaciones | SQLite, decoradores, arranque FastAPI | Filtros, orden, resumen, componente ReactPy |
| Temas que defiende | Inmutabilidad · Ausencia de valor · Pattern matching · Manejo funcional de errores | Decoradores · Pureza y efectos secundarios | Funciones de orden superior · Lambdas · Closures |
| Revisa el PR de | C | A | B |

Cada integrante debe poder explicar **también** los temas de los otros dos: la revisión cruzada existe para eso.

## 3. Contrato entre ramas (firmas congeladas)

Estas firmas permiten trabajar en paralelo. Cambiarlas requiere acuerdo de los tres.

| Módulo | Contrato |
|---|---|
| `core` | `Task`, `Priority`, `Ok`, `Err`, `bind`, `map_result`, `option_map`, `option_or`, `build_task(form) -> Result[Task]`, `toggle_completed`, `add_task`, `replace_task`, `remove_task`, `task_from_row(row) -> Task` |
| `decorators` | `logged`, `catching(*excepciones, message=...)` |
| `db` | `init_db()`, `insert_task(Task)`, `list_tasks()`, `set_completed(id, bool)`, `delete_task(id)`; todas devuelven `Result` |
| `queries` | `apply_filters(tasks, status, priority, category)`, `sort_tasks(tasks, key)`, `categories_of`, `due_status(task, today)`, `summarize(tasks, today)` |

Dependencias: `core` no depende de nadie · `queries` y `decorators` dependen de `core` · `db` depende de `core` y `decorators` · `ui` depende de `core`, `queries` y `db`.

## 4. Orden de integración

1. **A** abre PR de `feature/dominio-core` hacia `develop` (es la base de todos).
2. **B** y **C** actualizan su rama con `git rebase develop` y abren sus PR.
3. Con las tres ramas en `develop`: `python -m pytest -q` en verde y prueba manual con `uvicorn main:app --reload`.
4. Se fusiona `develop` en `main`.

## 5. Puesta en marcha

Una persona crea el repositorio con la base (ver sección 7). Luego cada integrante, en su clon:

```bash
git checkout develop && git pull
scripts/ramas.sh a ../gestor_tareas_completo     # o b / c, según su rol
git commit -m "feat: <qué aportas>"              # con TU identidad de git
git push -u origin feature/<tu-rama>
```

## 6. Reglas de calidad (Definition of Done)

- `python -m pytest -q` en verde antes de abrir el PR.
- `core.py` y `queries.py` **no importan** `sqlite3`, `reactpy`, `os`, `logging` ni leen el reloj. Lo verifica `test_architecture.py`.
- Mensajes de commit convencionales: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`.
- Todo PR lo aprueba al menos otro integrante, siguiendo la tabla de revisión.
- Cada función nueva nace con su prueba.

## 7. Creación del repositorio base (una sola vez)

```bash
git init -b main
git add README.md requirements.txt .gitignore docs scripts gestor/__init__.py tests/__init__.py
git commit -m "chore: estructura base del proyecto"
git remote add origin <URL_DEL_REPO> && git push -u origin main
git checkout -b develop && git push -u origin develop
```

## 8. Mejoras siguientes (dificultad progresiva)

| Nivel | A: Dominio | B: Shell | C: Consultas e interfaz |
|---|---|---|---|
| 1 | Rechazar fecha límite anterior a hoy (`today` como parámetro de `build_task`) | Guardar versión del esquema en SQLite | Predicado puro de filtro por rango de fechas |
| 2 | `edit_task(task, form) -> Result[Task]` | `update_task` en `db` + decorador `@transactional` | Ordenación seleccionable desde la UI, pasando `key` |
| 3 | Pruebas basadas en propiedades con `hypothesis` | Decorador `@retry(n)` para base bloqueada | Dividir `TaskApp` en componentes con *props* y `use_reducer` |

La edición de tareas (nivel 2) atraviesa las tres ramas: coordinen primero el contrato y luego implementen en paralelo.
