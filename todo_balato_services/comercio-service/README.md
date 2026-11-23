# Servicio de Comercio

Servicio Django responsable de las operaciones de carrito y checkout. Usa base de datos relacional (`COMERCIO_DATABASE_URL`, con PostgreSQL en `comercio_db` o SQLite local en desarrollo) y consulta los datos de productos a `catalogo-service` vía HTTP (`ordenes/catalogo_client.py`), sin acceso directo a MongoDB (MongoDB pertenece exclusivamente a `catalogo-service`).

## Variables de entorno

Completa `.env` a partir de `.env.example` con los valores correspondientes:

- `COMERCIO_DATABASE_URL`: cadena de conexión de base de datos para Comercio (por ejemplo, PostgreSQL en `comercio_db` o `sqlite:///comercio_db.sqlite3` en desarrollo local).
- `CATALOGO_API_URL`: URL base de la API de `catalogo-service`.
  - Ejemplo: `CATALOGO_API_URL=http://localhost:8002/api`
- `JWT_SIGNING_KEY`: debe ser exactamente la misma clave configurada en Gestión.

No incluyas configuraciones ni credenciales de conexión directa a MongoDB en Comercio, no uses valores de ejemplo como credenciales reales y no compartas el archivo `.env`.

## Configuración local

Ubicado en `comercio-service`:

### En macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### En Windows (CMD)

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Si usas PowerShell y aparece un error indicando que la ejecución de scripts está bloqueada, permite la activación solo en esa terminal y activa el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

El cambio de política termina al cerrar esa terminal. En CMD, usa `venv\Scripts\activate.bat` como en los comandos de configuración.

## Migraciones e inicio

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

La API local queda disponible bajo `[http://127.0.0.1:8001/api/](http://127.0.0.1:8001/api/)`.

Para desarrollo local, CORS permite los orígenes de Vite `http://localhost:5173` y `[http://127.0.0.1:5173](http://127.0.0.1:5173)`.

## Integración con Catálogo (HTTP)

- **Endpoint consumido:** `GET {CATALOGO_API_URL}/productos/<producto_id>/` (endpoint de lectura de `catalogo-service`).
- **Formato de datos esperado / normalizado:** el cliente valida la respuesta HTTP y trabaja con los campos mínimos:
  - `identificador`
  - `nombre`
  - `precio`
  - `moneda`
  - `estado`
  - `stock_disponible`
- **Manejo explícito de errores:** ante `404` (producto no encontrado), respuestas JSON/campos inválidos o caída/timeout de `catalogo-service`, se lanzan excepciones explícitas (`ProductoNoEncontradoError`, `RespuestaCatalogoInvalidaError`, `CatalogoNoDisponibleError`) sin convertirlos en productos vacíos ni en falsos éxitos; en `POST /api/carrito/calcular`, los ítems inexistentes se reportan con `problema: "no_existe"` (`puede_pagar: false`) y la falta de disponibilidad de Catálogo responde `503 Service Unavailable`.

### Verificación sin acceso directo a MongoDB

1. Confirma que `comercio-service` no tenga `pymongo` en `requirements.txt` ni conexiones/credenciales de MongoDB en `settings.py`, `.env`, `.env.example` o `importar_mock.py`.
2. Configura `CATALOGO_API_URL` en `.env` (por ejemplo, `http://localhost:8002/api`) y levanta `catalogo-service` (`8002`) y `comercio-service` (`8001`).
3. Prueba `POST /api/carrito/calcular` (y `POST /api/checkout` cuando aplique) en `comercio-service` con un `producto_id` existente, con uno inexistente (`200` con `problema: "no_existe"`) y con `catalogo-service` detenido (`503`) para verificar que la comunicación ocurre por HTTP y los errores se reportan explícitamente sin que Comercio acceda a MongoDB.

## Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/carrito/calcular` | Calcula el carrito con productos consultados a Catálogo |
| POST | `/api/checkout` | Procesa la solicitud de checkout autenticada |

El checkout requiere un JWT válido emitido por Gestión y la cabecera `Idempotency-Key`. Consulta los contratos y validaciones del código antes de integrar un cliente.
