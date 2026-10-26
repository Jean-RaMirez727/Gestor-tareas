"""Punto de entrada. FastAPI solo integra y sirve la app ReactPy (sin API REST propia).

Ejecutar:  uvicorn main:app --reload
"""
import logging

from fastapi import FastAPI
from reactpy import html
from reactpy.backend.fastapi import Options, configure

from gestor import db
from gestor.core import Err
from gestor.ui import CSS, TaskApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

match db.init_db():
    case Err(error):
        raise SystemExit(error)

app = FastAPI(title="Gestor de tareas")
configure(
    app,
    TaskApp,
    Options(
        head=(
            html.meta({"charset": "utf-8"}),
            html.meta({"name": "viewport", "content": "width=device-width, initial-scale=1"}),
            html.title("Gestor de tareas"),
            html.style(CSS),
        )
    ),
)
