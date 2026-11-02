import re
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


def registrar_compra(tipo_id, cantidad, nombre, correo):
    """Comprueba las reglas, descuenta las plazas y guarda la compra.

    Devuelve (compra, None) si va bien, o (None, (código, mensaje)) si no.
    Nombre y correo ya llegan validados.
    """
    entrada = buscar_entrada(tipo_id)
    if entrada is None:
        return None, (422, "Ese tipo de entrada no existe.")
    if cantidad < 1 or cantidad > entrada["max_por_compra"]:
        return None, (422, f"La cantidad tiene que estar entre 1 y {entrada['max_por_compra']}.")
    with CANDADO:  # comprobar y descontar a la vez, para no vender plazas que ya no hay
        if entrada["plazas_libres"] == 0:
            return None, (409, f"La entrada «{entrada['nombre']}» está agotada.")
        if cantidad > entrada["plazas_libres"]:
            return None, (409, f"Solo quedan {entrada['plazas_libres']} plazas de «{entrada['nombre']}».")
        entrada["plazas_libres"] -= cantidad
        compra = {
            "id": siguiente_id(),
            "tipo_id": entrada["id"],
            "cantidad": cantidad,
            "total": calcular_total(entrada, cantidad),
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "nombre": nombre,
            "correo": correo,
        }
        COMPRAS.append(compra)
    return compra, None


@app.get("/salud")
def salud():
    return {"ok": True, "app": "Entradas SOINU"}


# ---------- API JSON ----------

@app.get("/api/entradas")
def api_entradas():
    return ENTRADAS


@app.get("/api/entradas/{entrada_id}")
def api_entrada(entrada_id: int):
    entrada = buscar_entrada(entrada_id)
    if entrada is None:
        raise HTTPException(status_code=404, detail="No existe ese tipo de entrada")
    return entrada


@app.post("/api/compras", status_code=201)
def api_crear_compra(nueva: CompraNueva):
    compra, error = registrar_compra(nueva.tipo_id, nueva.cantidad, nueva.nombre.strip(), nueva.correo.strip())
    if error:
        codigo, mensaje = error
        raise HTTPException(status_code=codigo, detail=mensaje)
    return compra


@app.get("/api/compras/{compra_id}")
def api_compra(compra_id: int):
    compra = buscar_compra(compra_id)
    if compra is None:
        raise HTTPException(status_code=404, detail="No existe esa compra")
    return compra


# ---------- PÁGINAS ----------

def pagina_error(request, titulo, mensaje, codigo=404):
    return templates.TemplateResponse(
        request, "error.html", {"titulo": titulo, "mensaje": mensaje}, status_code=codigo
    )


def a_entero(texto):
    """'3' -> 3; cualquier otra cosa -> None (para dar una página de error y no un volcado)."""
    return int(texto) if texto.isdigit() else None


@app.get("/", response_class=HTMLResponse)
def portada(request: Request):
    return templates.TemplateResponse(request, "index.html", {"entradas": ENTRADAS})


@app.get("/entradas/{entrada_id}", response_class=HTMLResponse)
def pagina_entrada(request: Request, entrada_id: str):
    entrada = buscar_entrada(a_entero(entrada_id))
    if entrada is None:
        return pagina_error(request, "Esa entrada no existe",
                            "El tipo de entrada que buscas no existe o ya no está a la venta.")
    return templates.TemplateResponse(request, "entrada.html", {"entrada": entrada})


# ---------- COMPRAR (POST-redirect-GET) ----------

def formulario_compra(request, datos, error=None, codigo=200):
    return templates.TemplateResponse(
        request, "comprar.html",
        {"entradas": ENTRADAS, "datos": datos, "error": error},
        status_code=codigo,
    )


@app.get("/comprar", response_class=HTMLResponse)
def pagina_comprar(request: Request, tipo: str = ""):
    return formulario_compra(request, {"tipo_id": tipo, "cantidad": 1, "nombre": "", "correo": ""})


@app.post("/comprar", response_class=HTMLResponse)
def comprar(request: Request, tipo_id: str = Form(""), cantidad: str = Form(""),
            nombre: str = Form(""), correo: str = Form("")):
    datos = {"tipo_id": tipo_id.strip(), "cantidad": cantidad.strip(),
             "nombre": nombre.strip(), "correo": correo.strip()}

    # Mismas reglas que CompraNueva, pero el error se pinta en la página
    error = None
    tipo, num = a_entero(datos["tipo_id"]), a_entero(datos["cantidad"])
    if tipo is None:
        error = "Elige un tipo de entrada."
    elif num is None or num < 1:
        error = "La cantidad tiene que ser un número entero de 1 en adelante."
    elif not 2 <= len(datos["nombre"]) <= 60:
        error = "Escribe tu nombre (entre 2 y 60 caracteres)."
    elif len(datos["correo"]) > 120 or not re.fullmatch(PATRON_CORREO, datos["correo"]):
        error = "Ese correo no es válido. Ejemplo: nombre@dominio.com"

    if error is None:
        compra, fallo = registrar_compra(tipo, num, datos["nombre"], datos["correo"])
        if fallo is None:
            return RedirectResponse(f"/compra/{compra['id']}", status_code=303)
        error = fallo[1]

    return formulario_compra(request, datos, error, codigo=400)


@app.get("/compra/{compra_id}", response_class=HTMLResponse)
def confirmacion(request: Request, compra_id: str):
    compra = buscar_compra(a_entero(compra_id))
    if compra is None:
        return pagina_error(request, "Esa compra no existe", "No hay ninguna compra con ese número.")
    entrada = buscar_entrada(compra["tipo_id"])
    return templates.TemplateResponse(request, "confirmacion.html", {"compra": compra, "entrada": entrada})


# ---------- PRUEBA (en tu ordenador: python main.py) ----------
if __name__ == "__main__":
    from aula import Cliente
    c = Cliente(app)
    print(c.get("/salud").json())
    print(c.get("/api/entradas").status_code, "tipos:", len(c.get("/api/entradas").json()))
    print(c.get("/api/entradas/99").status_code, "(esperado 404)")
    r = c.post("/api/compras", json={"tipo_id": 4, "cantidad": 2, "nombre": "Ane", "correo": "ane@ejemplo.com",
                                     "total": 1})  # el total que llega se ignora
    print(r.status_code, r.json())
    print(c.post("/api/compras", json={"tipo_id": 4, "cantidad": 2, "nombre": "Ane", "correo": "sin-arroba"})
          .status_code, "(esperado 422)")
    print(c.get(f"/api/compras/{r.json()['id']}").status_code, "(esperado 200)")
    print(c.get("/").status_code, c.get("/entradas/1").status_code, "(esperado 200 200)")
    print(c.get("/entradas/99").status_code, c.get("/entradas/abc").status_code, "(esperado 404 404)")

    # Formulario (el Cliente sigue la redirección 303 hasta la confirmación)
    r = c.post("/comprar", data={"tipo_id": "1", "cantidad": "3", "nombre": "Iker", "correo": "iker@ejemplo.com"})
    print(r.status_code, r.url, "75 €" in r.text, "(esperado 200 .../compra/2 True)")
    antes = len(COMPRAS)
    c.get(str(r.url))
    print("recargar no repite la compra:", len(COMPRAS) == antes)
    r = c.post("/comprar", data={"tipo_id": "1", "cantidad": "3", "nombre": "Iker", "correo": "mal"})
    print(r.status_code, "Iker" in r.text, "(esperado 400 True: error en la página sin perder lo escrito)")
    r = c.post("/comprar", data={"tipo_id": "4", "cantidad": "2", "nombre": "Mikel", "correo": "m@e.com"})
    while r.status_code == 200:  # comprar VIP hasta agotarla
        r = c.post("/comprar", data={"tipo_id": "4", "cantidad": "2", "nombre": "Mikel", "correo": "m@e.com"})
    print(r.status_code, buscar_entrada(4)["plazas_libres"], "Agotada" in c.get("/").text,
          "(esperado 400 0 True)")
    print(c.post("/api/compras", json={"tipo_id": 4, "cantidad": 1, "nombre": "Ane", "correo": "a@e.com"})
          .status_code, "(esperado 409)")
