from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Muro de Eder Olivencia")

class MensajeNuevo(BaseModel):
    autor: str
    texto: str

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

from fastapi import FastAPI, HTTPException   # ← cambia la línea de arriba del archivo

@app.get("/api/mensajes/{mensaje_id}")
def ver_mensaje(mensaje_id: int):
    for m in MENSAJES:
        if m["id"] == mensaje_id:
            return m
    raise HTTPException(status_code=404, detail="No existe ese mensaje")