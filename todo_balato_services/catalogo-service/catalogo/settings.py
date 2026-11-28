import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "productos",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]

ROOT_URLCONF = "catalogo.urls"
WSGI_APPLICATION = "catalogo.wsgi.application"

# MongoDB es la única base de este servicio; no se usa el ORM de Django.
DATABASES = {}
CATALOGO_MONGO_URI = os.getenv("CATALOGO_MONGO_URI", "")
CATALOGO_DB_NAME = os.getenv("CATALOGO_DB_NAME", "catalogo_db")
CATALOGO_RESERVAS_COLLECTION = os.getenv("CATALOGO_RESERVAS_COLLECTION", "reservas")
CATALOGO_SERVICIO_TOKEN = os.getenv("CATALOGO_SERVICIO_TOKEN", "")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "productos.errors.manejador_excepciones",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"pymongo": {"level": "WARNING"}},
}

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_TZ = True
