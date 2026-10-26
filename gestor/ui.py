"""IMPERATIVE SHELL - interfaz ReactPy: estado, eventos y efectos."""
from __future__ import annotations

from datetime import date
from types import MappingProxyType
from typing import Callable

from reactpy import component, html, use_state

from . import db
from .core import Err, Ok, Task, add_task, bind, build_task, option_map, remove_task, replace_task, toggle_completed
from .queries import DueStatus, Summary, apply_filters, categories_of, due_status, sort_tasks, summarize

EMPTY_FORM = MappingProxyType({"title": "", "priority": "media", "category": "", "due_date": "", "notes": ""})

STATUS_OPTIONS = (("todas", "Todas"), ("pendientes", "Pendientes"), ("completadas", "Completadas"))
PRIORITY_OPTIONS = (("alta", "Alta"), ("media", "Media"), ("baja", "Baja"))

CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: #0f1115; color: #e6e8ee; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.app { max-width: 880px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { margin: 0 0 4px; font-size: 28px; letter-spacing: -0.02em; }
.subtitle { margin: 0 0 24px; color: #8b93a7; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat { background: #181b22; border: 1px solid #262b36; border-radius: 12px; padding: 14px 16px; }
.stat b { display: block; font-size: 24px; }
.stat span { color: #8b93a7; font-size: 13px; }
.stat.warn b { color: #ff6b6b; }
.card { background: #181b22; border: 1px solid #262b36; border-radius: 14px; padding: 18px; margin-bottom: 20px; }
.card h2 { margin: 0 0 14px; font-size: 16px; color: #c3c9d9; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
label { display: block; font-size: 12px; color: #8b93a7; margin-bottom: 4px; }
input, select, textarea { width: 100%; background: #0f1115; color: #e6e8ee; border: 1px solid #2c3240; border-radius: 8px; padding: 9px 10px; font: inherit; }
input:focus, select:focus, textarea:focus { outline: 2px solid #7c5cff55; border-color: #7c5cff; }
textarea { resize: vertical; }
.full { grid-column: 1 / -1; }
button { cursor: pointer; border: 1px solid #2c3240; background: #222735; color: #e6e8ee; border-radius: 8px; padding: 8px 14px; font: inherit; }
button:hover { background: #2b3144; }
button.primary { background: #7c5cff; border-color: #7c5cff; color: white; font-weight: 600; }
button.primary:hover { background: #6a49f0; }
button.danger:hover { background: #4a2328; border-color: #ff6b6b; color: #ff9b9b; }
.alert { padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.alert.ok { background: #12301f; border: 1px solid #1f6b3e; color: #7de2a8; }
.alert.error { background: #3a1a1e; border: 1px solid #8a2e38; color: #ff9b9b; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.task { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; background: #181b22; border: 1px solid #262b36; border-left: 4px solid #444; border-radius: 12px; padding: 14px 16px; }
.task.prio-alta { border-left-color: #ff6b6b; }
.task.prio-media { border-left-color: #ffb454; }
.task.prio-baja { border-left-color: #4cd4a0; }
.task.done .title { text-decoration: line-through; color: #7a8196; }
.title { font-weight: 600; margin-bottom: 6px; }
.notes { color: #9aa2b8; font-size: 14px; margin: 6px 0 0; white-space: pre-wrap; }
.badges { display: flex; flex-wrap: wrap; gap: 6px; }
.badge { font-size: 12px; padding: 2px 9px; border-radius: 999px; background: #222735; color: #b6bdd0; }
.badge.vencida { background: #3a1a1e; color: #ff9b9b; }
.badge.vence-hoy { background: #3b2d12; color: #ffc878; }
.badge.completada { background: #12301f; color: #7de2a8; }
.actions { display: flex; gap: 8px; flex-shrink: 0; }
.empty { text-align: center; color: #7a8196; padding: 28px; border: 1px dashed #2c3240; border-radius: 12px; }
@media (max-width: 600px) { .stats { grid-template-columns: repeat(2, 1fr); } .task { flex-direction: column; } }
"""


# --------------------------------------------------------------------------- #
# Ayudantes de la vista
# --------------------------------------------------------------------------- #
def value_of(event: dict) -> str:
    return event["target"]["value"]


def field_updater(set_form: Callable, key: str) -> Callable:
    """Closure: recuerda `key` y produce el manejador de ese campo."""
    return lambda event: set_form(lambda form: {**form, key: value_of(event)})


def options(pairs: tuple[tuple[str, str], ...]) -> list:
    return [html.option({"value": value, "key": value}, label) for value, label in pairs]


def field(label: str, control, extra_class: str = ""):
    return html.div({"class_name": extra_class}, html.label(label), control)


def load_initial_tasks() -> tuple[Task, ...]:
    match db.list_tasks():
        case Ok(tasks):
            return tasks
        case Err():
            return ()


def stats_view(summary: Summary):
    cells = (
        ("Total", summary.total, ""),
        ("Pendientes", summary.pending, ""),
        ("Completadas", summary.completed, ""),
        ("Vencidas", summary.overdue, "warn" if summary.overdue else ""),
    )
    return html.div(
        {"class_name": "stats"},
        *[html.div({"class_name": f"stat {extra}", "key": name}, html.b(str(n)), html.span(name)) for name, n, extra in cells],
    )


def due_badge(task: Task, today: date):
    match due_status(task, today):
        case DueStatus.NO_DATE | DueStatus.COMPLETED:
            return None
        case status:
            css = status.value.replace(" ", "-")
            text = option_map(task.due_date, lambda d: f"{status.value} · {d:%d/%m/%Y}")
            return html.span({"class_name": f"badge {css}"}, text)


def task_view(task: Task, today: date, on_toggle: Callable, on_delete: Callable):
    return html.li(
        {"key": str(task.id), "class_name": f"task prio-{task.priority.value}{' done' if task.completed else ''}"},
        html.div(
            html.div({"class_name": "title"}, task.title),
            html.div(
                {"class_name": "badges"},
                html.span({"class_name": "badge"}, f"Prioridad {task.priority.value}"),
                html.span({"class_name": "badge"}, task.category),
                due_badge(task, today),
                html.span({"class_name": "badge completada"}, "Completada") if task.completed else None,
            ),
            option_map(task.notes, lambda notes: html.p({"class_name": "notes"}, notes)),
        ),
        html.div(
            {"class_name": "actions"},
            html.button({"on_click": on_toggle}, "Reabrir" if task.completed else "Completar"),
            html.button({"class_name": "danger", "on_click": on_delete}, "Eliminar"),
        ),
    )


# --------------------------------------------------------------------------- #
# Componente raíz
# --------------------------------------------------------------------------- #
@component
def TaskApp():
    today = date.today()  # efecto externo: se lee aquí y se inyecta al núcleo puro
    tasks, set_tasks = use_state(load_initial_tasks)
    form, set_form = use_state(EMPTY_FORM)
    status, set_status = use_state("todas")
    priority_filter, set_priority_filter = use_state("todas")
    category_filter, set_category_filter = use_state("todas")
    message, set_message = use_state(None)  # None = no hay mensaje que mostrar

    def notify(kind: str, text: str) -> None:
        set_message((kind, text))

    def handle_add(_event) -> None:
        match bind(build_task(form), db.insert_task):
            case Ok(task):
                set_tasks(lambda current: add_task(current, task))
                set_form(EMPTY_FORM)
                notify("ok", f"Tarea «{task.title}» creada.")
            case Err(error):
                notify("error", error)

    def make_toggle_handler(task: Task) -> Callable:
        def handler(_event) -> None:
            updated = toggle_completed(task)
            match db.set_completed(task.id, updated.completed):
                case Ok(_):
                    set_tasks(lambda current: replace_task(current, updated))
                    notify("ok", f"Tarea «{task.title}» {'completada' if updated.completed else 'reabierta'}.")
                case Err(error):
                    notify("error", error)

        return handler

    def make_delete_handler(task: Task) -> Callable:
        def handler(_event) -> None:
            match db.delete_task(task.id):
                case Ok(_):
                    set_tasks(lambda current: remove_task(current, task.id))
                    notify("ok", f"Tarea «{task.title}» eliminada.")
                case Err(error):
                    notify("error", error)

        return handler

    visible = sort_tasks(apply_filters(tasks, status, priority_filter, category_filter))
    category_options = (("todas", "Todas"), *((c, c) for c in categories_of(tasks)))

    banner = option_map(message, lambda m: html.div({"class_name": f"alert {m[0]}"}, m[1]))

    form_card = html.div(
        {"class_name": "card"},
        html.h2("Nueva tarea"),
        html.div(
            {"class_name": "grid"},
            field(
                "Título",
                html.input({"value": form["title"], "placeholder": "¿Qué hay que hacer?", "max_length": 80, "on_change": field_updater(set_form, "title")}),
                "full",
            ),
            field("Prioridad", html.select({"value": form["priority"], "on_change": field_updater(set_form, "priority")}, *options(PRIORITY_OPTIONS))),
            field("Categoría", html.input({"value": form["category"], "placeholder": "General", "max_length": 30, "on_change": field_updater(set_form, "category")})),
            field("Fecha límite", html.input({"type": "date", "value": form["due_date"], "on_change": field_updater(set_form, "due_date")})),
            field("Descripción o notas", html.textarea({"value": form["notes"], "rows": 3, "on_change": field_updater(set_form, "notes")}), "full"),
        ),
        html.div({"style": {"marginTop": "14px"}}, html.button({"class_name": "primary", "on_click": handle_add}, "Agregar tarea")),
    )

    filters_card = html.div(
        {"class_name": "card"},
        html.h2("Filtros"),
        html.div(
            {"class_name": "grid"},
            field("Estado", html.select({"value": status, "on_change": lambda e: set_status(value_of(e))}, *options(STATUS_OPTIONS))),
            field("Prioridad", html.select({"value": priority_filter, "on_change": lambda e: set_priority_filter(value_of(e))}, *options((("todas", "Todas"), *PRIORITY_OPTIONS)))),
            field("Categoría", html.select({"value": category_filter, "on_change": lambda e: set_category_filter(value_of(e))}, *options(category_options))),
        ),
    )

    task_list = (
        html.ul(*[task_view(t, today, make_toggle_handler(t), make_delete_handler(t)) for t in visible])
        if visible
        else html.div({"class_name": "empty"}, "No hay tareas que coincidan con los filtros actuales.")
    )

    return html.div(
        {"class_name": "app"},
        html.h1("Gestor de tareas y actividades"),
        html.p({"class_name": "subtitle"}, "Registra, prioriza y completa tus tareas."),
        stats_view(summarize(tasks, today)),
        banner,
        form_card,
        filters_card,
        task_list,
    )
