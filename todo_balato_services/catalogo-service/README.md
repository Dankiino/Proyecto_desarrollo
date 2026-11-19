# Catálogo Service

Servicio Django independiente de **Catálogo e Inventario**. Es el único que accede a MongoDB (`catalogo_db`); Gestión, Comercio y React lo consumen solo por HTTP.
Tiene su propio proyecto, dependencias, configuración y entorno virtual.

## Estructura

```
catalogo-service/
├── manage.py
├── requirements.txt     # dependencias propias
├── .env.example         # plantilla de variables (copiar a .env)
├── catalogo/            # proyecto Django (settings, urls, wsgi)
└── productos/           # app: productos, existencias, reservas y movimientos
    ├── urls.py
    └── views.py         # HealthView
```

## Requisitos

- Windows y Python 3.12 o superior
- Acceso a MongoDB Atlas (no se necesita para la ruta de estado)

Versiones fijadas: Django 6.1.2, DRF 3.18.3, django-cors-headers 4.9.0, python-dotenv 1.2.4 y pymongo 4.19.0, las mismas que usan Gestión y Comercio.

## Instalación (CMD)

Desde `todo_balato_services`:

```cmd
cd catalogo-service
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Ejecuta `copy .env.example .env` solo si aún no existe `.env`. Completa `.env` con tus valores locales; no lo subas al repositorio.
Si PowerShell bloquea la activación, usa CMD o `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

## Configuración (`.env`)

| Variable | Descripción |
|---|---|
| `CATALOGO_MONGO_URI` | URI privada de MongoDB Atlas |
| `CATALOGO_DB_NAME` | Base de datos (`catalogo_db`) |
| `DJANGO_SECRET_KEY` | Clave secreta de Django (obligatoria) |
| `DJANGO_DEBUG` | `True` solo en local |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por coma |
| `CORS_ALLOWED_ORIGINS` | Orígenes de React, separados por coma |

## Iniciar el servicio

```cmd
cd catalogo-service
venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8002
```

Usa su propio `venv`: no hace falta activar los de Gestión ni Comercio. Puerto 8002 (Gestión usa 8000 y Comercio 8001).

## Ruta de estado

`GET http://127.0.0.1:8002/api/health`

```json
{"status": "ok", "service": "catalogo-service"}
```
