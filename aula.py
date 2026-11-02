"""El `Cliente` del bloque PRUEBA de main.py en tu ordenador: el mismo que usa el Aula, aquí con el TestClient de FastAPI.

    from aula import Cliente
    c = Cliente(app)
    print(c.get("/salud").json())
"""
from fastapi.testclient import TestClient as Cliente  # noqa: F401  (sigue las redirecciones, como el navegador)
