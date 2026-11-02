from datetime import datetime
from threading import Lock

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="Entradas SOINU")
templates = Jinja2Templates(directory="templates")


# ---------- DATOS ----------

ENTRADAS = [
    {
        "id": 1,
        "nombre": "General (1 día)",
        "descripcion_corta": "Acceso a la pista un día a elegir.",
        "descripcion": "Entrada de un día para la pista del festival. Elige el día al entrar; "
                       "con la pulsera puedes salir y volver a entrar ese mismo día.",
        "precio": 25,
        "plazas_totales": 300,
        "plazas_libres": 300,
        "max_por_compra": 6,
        "dias": "Un día a elegir",
        "zona": "Pista",
    },
    {
        "id": 2,
        "nombre": "Adaptada",
        "descripcion_corta": "Zona accesible; el acompañante entra gratis.",
        "descripcion": "Entrada para personas con movilidad reducida o necesidades de accesibilidad. "
                       "Plataforma elevada con buena visibilidad, acceso directo sin escaleras y aseos "
                       "adaptados al lado. Incluye la entrada gratuita de un acompañante.",
        "precio": 20,
        "plazas_totales": 20,
        "plazas_libres": 20,
        "max_por_compra": 2,
        "dias": "Un día a elegir",
        "zona": "Plataforma accesible",
    },
    {
        "id": 3,
        "nombre": "Abono 3 días",
        "descripcion_corta": "Los tres días del festival por menos.",
        "descripcion": "Abono para los tres días del festival con acceso a la pista. "
                       "Sale más barato que comprar tres entradas generales.",
        "precio": 60,
        "plazas_totales": 150,
        "plazas_libres": 150,
        "max_por_compra": 4,
        "dias": "Los tres días",
        "zona": "Pista",
    },
    {
        "id": 4,
        "nombre": "VIP",
        "descripcion_corta": "Zona VIP con barra propia y una consumición.",
        "descripcion": "Acceso a la zona VIP junto al escenario, con barra y aseos propios "
                       "y una consumición incluida. Válida para un día a elegir.",
        "precio": 90,
        "plazas_totales": 30,
        "plazas_libres": 30,
        "max_por_compra": 2,
        "dias": "Un día a elegir",
        "zona": "Zona VIP",
    },
]

COMPRAS = []  # vacía al arrancar

# Para que dos compras a la vez no vendan la misma plaza
CANDADO = Lock()

PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class CompraNueva(BaseModel):
    """Lo que manda el comprador. No hay precio ni total: el total lo calcula el servidor."""
    tipo_id: int
    cantidad: int = Field(ge=1, le=6)
    nombre: str = Field(min_length=2, max_length=60)
    correo: str = Field(max_length=120, pattern=PATRON_CORREO)


def siguiente_id():
    return max((c["id"] for c in COMPRAS), default=0) + 1


def buscar_entrada(entrada_id):
    for e in ENTRADAS:
        if e["id"] == entrada_id:
            return e
    return None


def buscar_compra(compra_id):
    for c in COMPRAS:
        if c["id"] == compra_id:
            return c
    return None


def calcular_total(entrada, cantidad):
    return entrada["precio"] * cantidad


@app.get("/salud")
def salud():
    return {"ok": True, "app": "Entradas SOINU"}


# ---------- PRUEBA (en tu ordenador: python main.py) ----------
if __name__ == "__main__":
    from aula import Cliente
    c = Cliente(app)
    print(c.get("/salud").json())
