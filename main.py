from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="Muro")
templates = Jinja2Templates(directory="templates")

app = FastAPI(title="Muro de Eder Olivencia")

class MensajeNuevo(BaseModel):
    autor: str = Field(min_length=1, max_length=30)
    texto: str = Field(min_length=1, max_length=280)

MENSAJES = [
    {"id": 1, "autor": "Ane", "texto": "Bienvenidos al muro de 2.º DAM"},
    {"id": 2, "autor": "Iker", "texto": "¿Alguien ha conseguido arrancar uvicorn?"},
]

def siguiente_id():
    return max((m["id"] for m in MENSAJES), default=0) + 1
# 1. GET /salud → {"ok": True, "app": "Muro"}


# ---------- PRUEBA (en el Aula; en tu ordenador: python main.py) ----------
if __name__ == "__main__":
    from aula import Cliente
    c = Cliente(app)
    print(c.get("/salud").json())

@app.get("/salud")
def salud():
    return {"ok": True}

@app.get("/hola/{nombre}")
def hola(nombre: str):
    return {"saludo": f"Hola, {nombre}"}

@app.get("/api/mensajes")
def obtener_mensajes():
    return MENSAJES

@app.post("/api/mensajes")
def crear_mensaje(mensaje: MensajeNuevo):
    nuevo_mensaje = {
        "id": siguiente_id(),
        "autor": mensaje.autor,
        "texto": mensaje.texto
    }
    MENSAJES.append(nuevo_mensaje)
    return nuevo_mensaje

@app.get("/api/mensajes/{mensaje_id}")
def ver_mensaje(mensaje_id: int):
    for m in MENSAJES:
        if m["id"] == mensaje_id:
            return m
    raise HTTPException(status_code=404, detail="No existe ese mensaje")

@app.post("/api/mensajes", status_code=201)
def crear_mensaje(nuevo: MensajeNuevo):
    mensaje = {"id": siguiente_id(), **nuevo.model_dump()}
    MENSAJES.append(mensaje)
    return mensaje

@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse(request, "index.html", {"mensajes": MENSAJES})

@app.get("/mensajes/{mensaje_id}", response_class=HTMLResponse)
def detalle(request: Request, mensaje_id: int):
    for m in MENSAJES:
        if m["id"] == mensaje_id:
            return templates.TemplateResponse(request, "mensaje.html", {"mensaje": m})
    raise HTTPException(status_code=404, detail="No existe ese mensaje")