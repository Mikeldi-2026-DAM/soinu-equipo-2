# soinu-equipo-2 · Venta de entradas de SOINU

Web con FastAPI y Jinja2 para vender las entradas del festival SOINU. Parte del muro de mensajes de la semana 1
(2.º DAM): los mensajes se han cambiado por tipos de entrada y compras.

## Cómo se arranca

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abre <http://127.0.0.1:8000/> y, para probar la API, <http://127.0.0.1:8000/docs>.

## Entradas

### Tipos de entrada que se venden

| id | Nombre | Precio | Plazas | Máx. por compra | Qué incluye |
|----|--------|--------|--------|-----------------|-------------|
| 1 | General (1 día) | 25 € | 300 | 6 | Acceso a la pista un día a elegir. |
| 2 | Adaptada | 20 € | 20 | 2 | Zona accesible con buena visibilidad y acceso directo; el acompañante entra gratis. |
| 3 | Abono 3 días | 60 € | 150 | 4 | Acceso a la pista los tres días del festival. |
| 4 | VIP | 90 € | 30 | 2 | Zona VIP con barra propia, aseos y una consumición incluida. Un día. |

### Datos de cada tipo

- `id` (entero): para buscarlo en las rutas `/entradas/{id}`.
- `nombre`: lo que se ve en la tarjeta.
- `descripcion_corta`: una línea para la portada.
- `descripcion`: el texto completo de la página del tipo.
- `precio` (euros, entero): no hay precios con céntimos, así el total se calcula sin errores de redondeo.
- `plazas_totales` y `plazas_libres`: las libres bajan con cada compra; las totales no cambian y sirven para ver cuánto se ha vendido.
- `max_por_compra`: para que una sola persona no se lleve todas las entradas.
- `dias` y `zona`: el comprador necesita saber cuándo y dónde puede entrar.

### Datos de cada compra

- `id`, `tipo_id`, `cantidad`, `total` y `fecha` (fecha y hora en que se hizo).
- Del comprador, solo `nombre` y `correo`: el nombre para identificar la compra en la puerta y el correo para
  enviarle las entradas. No pedimos DNI, teléfono ni dirección porque no los necesitamos.

### Reglas

- **Cantidad**: mínimo 1 y máximo el `max_por_compra` del tipo (nunca más de 6).
- **Sin plazas**: si se piden más entradas de las que quedan libres, la compra no se hace (la API responde 409
  y el formulario muestra el error). Los tipos con 0 plazas libres salen como «Agotada» y no se pueden comprar.
- **Nombre**: obligatorio, entre 2 y 60 caracteres.
- **Correo**: obligatorio, con forma `algo@dominio.ext` (sin espacios, una sola @ y un punto después).
- **Total**: lo calcula siempre el servidor (`precio × cantidad`). Nunca se fía de un precio o total que llegue del
  formulario o de la API; si llega, se ignora.
- **Tipo**: tiene que existir; si no, la compra se rechaza.

## Rutas

| Ruta | Qué hace |
|------|----------|
| `GET /` | Portada: una tarjeta por tipo con precio y plazas libres («Agotada» si no quedan). |
| `GET /entradas/{id}` | Página del tipo con la descripción completa y el botón de comprar. |
| `GET /comprar?tipo={id}` | Formulario de compra. |
| `POST /comprar` | Guarda la compra y redirige con 303 a la confirmación; si algo falla, 400 con el error en la página. |
| `GET /compra/{id}` | Confirmación con el resumen y el total (recargarla no repite la compra). |
| `GET /api/entradas` | Lista de tipos en JSON (200). |
| `GET /api/entradas/{id}` | Un tipo (200 · 404). |
| `POST /api/compras` | Crea una compra (201 · 422 datos mal · 409 sin plazas). |
| `GET /api/compras/{id}` | Una compra (200 · 404). |

Para una prueba rápida sin navegador: `python main.py`.
