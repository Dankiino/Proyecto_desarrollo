# Catálogo Service

Servicio Django independiente de **Catálogo e Inventario**. Es el único que accede a MongoDB (`catalogo_db`); Gestión, Comercio y React lo consumen solo por HTTP.
Tiene su propio proyecto, dependencias, configuración y entorno virtual.

## Estructura

```text
catalogo-service/
├── manage.py
├── requirements.txt     # dependencias propias
├── .env.example         # plantilla de variables (copiar a .env)
├── catalogo/            # proyecto Django (settings, urls, wsgi)
└── productos/           # app: productos, existencias, reservas y movimientos
    ├── urls.py
    └── views.py         # HealthView, MongoHealthView
```

## Requisitos

- Python 3.12 o superior (macOS / Linux / Windows)
- Acceso a MongoDB Atlas (no se necesita para la ruta básica de estado `/api/health`)

Versiones fijadas: Django 6.1.2, DRF 3.18.3, django-cors-headers 4.9.0, python-dotenv 1.2.4 y pymongo 4.19.0.

## Instalación

Desde `todo_balato_services`:

### En macOS / Linux

```bash
cd catalogo-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### En Windows (CMD)

```cmd
cd catalogo-service
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Ejecuta la copia de `.env.example` a `.env` solo si aún no existe `.env`. Completa `.env` con tus valores locales; no lo subas al repositorio.
Si PowerShell bloquea la activación, usa CMD o `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

## Configuración (`.env`)

| Variable | Descripción |
|---|---|
| `CATALOGO_MONGO_URI` | URI privada de MongoDB Atlas (exclusiva de `catalogo-service`) |
| `CATALOGO_DB_NAME` | Base de datos (`catalogo_db`) |
| `DJANGO_SECRET_KEY` | Clave secreta de Django (obligatoria) |
| `DJANGO_DEBUG` | `True` solo en local |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por coma |
| `CORS_ALLOWED_ORIGINS` | Orígenes de React, separados por coma |

## Iniciar el servicio

### En macOS / Linux

```bash
cd catalogo-service
source venv/bin/activate
python manage.py runserver 127.0.0.1:8002
```

### En Windows (CMD)

```cmd
cd catalogo-service
venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8002
```

Usa su propio `venv`: no hace falta activar los de Gestión ni Comercio. Puerto 8002 (Gestión usa 8000 y Comercio 8001).

## Endpoints y consumo desde `comercio-service`

- **Rutas de salud expuestas:**
  - `GET [http://127.0.0.1:8002/api/health](http://127.0.0.1:8002/api/health)` -> `{"status": "ok", "service": "catalogo-service"}`
  - `GET [http://127.0.0.1:8002/api/health/mongo](http://127.0.0.1:8002/api/health/mongo)` -> verifica lectura en MongoDB desde `catalogo-service`
- **Endpoint de lectura consumido por `comercio-service`:**
  - `GET {CATALOGO_API_URL}/productos/<producto_id>/` (ejemplo local: `http://localhost:8002/api/productos/<producto_id>/`)
  - En `comercio-service`, se configura mediante la variable de entorno `CATALOGO_API_URL` (ejemplo: `CATALOGO_API_URL=http://localhost:8002/api`, sin credenciales ni valores privados).
- **Formato de datos esperado / devuelto:** `identificador`, `nombre`, `precio`, `moneda`, `estado`, `stock_disponible`.
- **Comportamiento ante errores o falta de disponibilidad:** si un producto no existe (`404` / no encontrado), la respuesta es inválida o `catalogo-service` no está disponible, `comercio-service` lo maneja explícitamente (por ejemplo, marcando el ítem como `no_existe` con `puede_pagar: false` en `POST /api/carrito/calcular` o devolviendo `503 Service Unavailable` cuando Catálogo está caído) sin convertirlo en productos vacíos ni en falsos éxitos.

## Verificación sin acceso directo de Comercio a MongoDB

1. Confirma que `comercio-service` no tenga `pymongo` ni variables/conexiones de MongoDB y que `catalogo-service` sea el único servicio con acceso a MongoDB.
2. Inicia `catalogo-service` en `127.0.0.1:8002` y `comercio-service` en `127.0.0.1:8001` con `CATALOGO_API_URL=http://localhost:8002/api`.
3. Prueba `POST /api/carrito/calcular` (y `POST /api/checkout` cuando aplique) en `comercio-service` con un producto existente, uno inexistente (`200` con `problema: "no_existe"`) y con `catalogo-service` detenido (`503`), validando que la comunicación ocurre vía HTTP y que los errores se reportan de forma explícita sin acceso directo de Comercio a MongoDB.
