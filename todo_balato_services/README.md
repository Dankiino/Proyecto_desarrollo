# Servicios Django de Todo Balato

Este repositorio contiene dos servicios Django independientes:

| Servicio | Carpeta | Responsabilidad | Base de datos |
|---|---|---|---|
| Gestión | [`gestion-service/`](./gestion-service/) | Registro, autenticación, usuarios y roles | PostgreSQL (`gestion_db`) |
| Comercio | [`comercio-service/`](./comercio-service/) | Cálculo de carrito y checkout | PostgreSQL (`comercio_db`) |

Comercio también consulta el catálogo almacenado en MongoDB Atlas (`catalogo_db`).
El servicio Django independiente de Catálogo aún está pendiente de crearse.

## Documentación por servicio

- [Gestión](./gestion-service/README.md): instalación, configuración y endpoints.
- [Comercio](./comercio-service/README.md): instalación, configuración y endpoints.

## Requisitos

- Windows, Python compatible con los requisitos fijados en cada servicio y `pip`.
- Acceso a las bases de datos del equipo.
- Los clientes `psql` y `mongosh` solo son necesarios para conectarse directamente
  desde consola; Django se conecta usando la configuración local de cada servicio.

## Configuración

Cada servicio tiene su propio entorno virtual y archivo `.env`. Desde una
terminal CMD, prepara Gestión:

```cmd
cd gestion-service
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Ejecuta `copy .env.example .env` solo si aún no existe `.env`; no sobrescribas
una configuración local existente.

Completa `gestion-service\.env` con la URL privada de PostgreSQL de Gestión y
una `JWT_SIGNING_KEY` fuerte. Comercio debe usar la misma clave JWT para validar
los tokens.

En otra terminal CMD, prepara Comercio:

```cmd
cd comercio-service
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Completa `comercio-service\.env` con la URL privada de PostgreSQL de Comercio,
la URI de MongoDB Atlas y exactamente la misma `JWT_SIGNING_KEY` configurada en
Gestión. No uses valores de ejemplo como credenciales reales.

### Si PowerShell bloquea la activación del entorno virtual

Si aparece un error indicando que no se pueden ejecutar scripts, en la
terminal PowerShell de ese servicio ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Hazlo dentro de la carpeta del servicio (`gestion-service` o
`comercio-service`). El cambio solo dura mientras esa terminal esté abierta.
Como alternativa, usa CMD y activa el entorno con
`venv\Scripts\activate.bat`.

## Iniciar los servicios

En una terminal CMD, inicia Gestión:

```cmd
cd gestion-service
venv\Scripts\activate.bat
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

En otra terminal CMD, inicia Comercio:

```cmd
cd comercio-service
venv\Scripts\activate.bat
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

URLs locales:

- Gestión: `http://127.0.0.1:8000/api/`
- Comercio: `http://127.0.0.1:8001/api/`

## Seguridad y datos

- No subas los archivos `.env` al repositorio ni compartas sus valores.
- No guardes contraseñas ni URI con credenciales en documentación o Jira.
- No ejecutes migraciones o scripts de carga en una base compartida sin
  autorización y confirmación del entorno.
