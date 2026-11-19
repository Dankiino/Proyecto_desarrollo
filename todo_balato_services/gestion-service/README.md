# Servicio de Gestión — Todo balato E-commerce

Servicio Django de gestión de usuarios y autenticación. Para una vista general
de ambos servicios, consulta el [README del repositorio](../README.md).

Microservicio independiente encargado de identidad, usuarios, roles, contenidos
administrables, temas visuales y mensajes de contacto. Forma parte de una
arquitectura de microservicios junto a los servicios **Comercio** (órdenes,
carrito, pagos) y **Catálogo** (productos, Mongo).

## Arquitectura

| Servicio | Base de datos | Responsabilidad |
|---|---|---|
| **Gestión** (este repo) | PostgreSQL — `gestion_db` (Neon) | Usuarios, autenticación, roles, contenidos, temas, contacto |
| Comercio | PostgreSQL — `comercio_db` (Neon, proyecto separado) | Carrito, órdenes, pagos |
| Catálogo (pendiente) | MongoDB — `catalogo_db` (Atlas) | Productos y stock; el servicio Django independiente está pendiente |

Gestión y Comercio son servicios Django independientes, con sus respectivas
bases de datos y credenciales. Catálogo aún no cuenta con un servicio Django
independiente; sus datos están en MongoDB Atlas. La separación futura debe
mantener la comunicación entre servicios vía API.

## Stack

- Python 3.13 + Django 6.1.2 + Django REST Framework 3.18.3
- PostgreSQL (Neon) vía `dj-database-url`
- Autenticación JWT vía `djangorestframework-simplejwt` (con blacklist de tokens)
- Variables de entorno vía `python-dotenv`

## Instalación desde clon limpio

El proyecto debe quedar organizado así dentro de la carpeta base
`todo_balato_Services`:

```text
todo_balato_Services\
├── gestion-service\
└── comercio-service\
```

Clona el repositorio completo con ese nombre y entra al servicio de Gestión:

```powershell
git clone <url-del-repo> todo_balato_Services
cd todo_balato_Services\gestion-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

En PowerShell, si aparece un error indicando que la ejecución de scripts está
deshabilitada, permite la ejecución solo en la terminal actual y vuelve a
activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

La opción `Process` no cambia la política de ejecución de forma permanente.
Si prefieres usar CMD, activa el entorno con:

```cmd
venv\Scripts\activate.bat
```

Completa `gestion-service\.env` con la URL real de PostgreSQL de Gestión y una
clave JWT compartida con Comercio. No publiques ni compartas el archivo `.env`.

Aplica las migraciones y, si aún no existe, crea el administrador:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### Iniciar los dos servicios en Windows

Cada servicio usa su propio entorno virtual y su propio archivo `.env`. Abre
una terminal para cada uno desde la carpeta base `todo_balato_Services`.

En la primera terminal, inicia Gestión:

```powershell
cd gestion-service
.\venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

En la segunda terminal, configura Comercio la primera vez:

```powershell
cd comercio-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Completa `comercio-service\.env` con las credenciales reales de Comercio y
Catálogo, y usa exactamente la misma `JWT_SIGNING_KEY` que en Gestión. Luego
aplica sus migraciones e inicia el servidor:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

Si PowerShell bloquea `Activate.ps1` en cualquiera de las terminales, ejecuta
allí `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y vuelve a
activar el entorno. En Símbolo del sistema (`cmd`), usa
`venv\Scripts\activate.bat` en lugar de `Activate.ps1`.

URLs locales:

- Gestión: `http://127.0.0.1:8000/api/`
- Comercio: `http://127.0.0.1:8001/api/`

Si cambias la carpeta base, usa el nombre que elegiste en los comandos `cd`;
los nombres `gestion-service` y `comercio-service` deben mantenerse.

## Variables de entorno

Gestión necesita `GESTION_DATABASE_URL` y `JWT_SIGNING_KEY`. Comercio necesita
`COMERCIO_DATABASE_URL`, `CATALOGO_MONGO_URI` y la misma `JWT_SIGNING_KEY`.
Los archivos `.env.example` de cada servicio muestran los nombres requeridos;
reemplaza sus valores de ejemplo por credenciales reales.

> No se versiona `.env`. Solo se versiona `.env.example` sin valores reales.

Para desarrollo local, Gestión permite mediante CORS los orígenes de Vite
`http://localhost:5173` y `http://127.0.0.1:5173`.

## Modelo de datos: usuarios

Esta sección describe cómo Gestión guarda a cada usuario en su base de datos
PostgreSQL. Un **modelo** es la definición que Django usa para crear y trabajar
con la tabla de usuarios; no es algo que debas configurar para iniciar el
servicio.

Cada fila de esa tabla representa una cuenta:

| Campo | Qué significa |
|---|---|
| `id` | Identificador único generado automáticamente; Django lo usa para distinguir cada cuenta. |
| `nombre`, `apellido` | Nombre y apellido de la persona. |
| `correo` | Correo para iniciar sesión. No se puede repetir y se usa en lugar de un nombre de usuario. |
| `rol` | Permisos generales de la cuenta: `CLIENTE` o `ADMIN`. El registro público crea clientes; el primer administrador se crea con `createsuperuser`. |
| `estado` | Situación de la cuenta: `PENDIENTE`, `ACTIVO` o `BLOQUEADO`. |
| `creado_en` | Fecha y hora en que se creó la cuenta; Django la asigna automáticamente. |
| `actualizado_en` | Fecha y hora de la última modificación; Django la actualiza automáticamente. |

La contraseña también se guarda en la tabla, pero Django almacena una versión
protegida (hash), no la contraseña legible. Además, el sistema incorpora campos
internos de autenticación y permisos de Django que no aparecen en la tabla
resumida de arriba.

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/api/registro` | público | Crea usuario, **siempre** rol `CLIENTE` (ignora cualquier `rol` enviado en el body) |
| POST | `/api/login` | público | Devuelve `access` + `refresh` JWT. Rechaza si `estado != ACTIVO` |
| POST | `/api/logout` | autenticado | Invalida (blacklist) el refresh token |
| GET | `/api/usuarios/me` | autenticado | Datos del usuario autenticado |
| GET | `/api/usuarios` | solo ADMIN activo | Lista todos los usuarios |
| POST | `/api/usuarios/:id/bloquear` | solo ADMIN activo | Bloquea un usuario |
| POST | `/api/usuarios/:id/desbloquear` | solo ADMIN activo | Reactiva un usuario |

## Reglas de negocio implementadas

- **RF07** — El registro público nunca crea administradores: el serializer ignora
  cualquier campo `rol` recibido y fuerza `CLIENTE`.
- **RF06 / RF14** — No se permite autobloqueo (`BloquearUsuarioView` compara
  `request.user.id` contra el id objetivo). No se permite bloquear al último
  administrador activo: antes de bloquear un `ADMIN`, se cuentan los
  `ADMIN` con `estado=ACTIVO` excluyendo al objetivo; si el conteo es 0, se
  rechaza con 400.
- **RF08** — Login rechaza credenciales inválidas o cuentas no activas, sin
  revelar si el correo existe.
- **RF10** — Autorización verificada en backend mediante permisos custom
  (`EsAdminActivo`, `EsClienteActivo`), no solo ocultando botones en el
  frontend. Probado con llamadas directas a la API sin y con token.
- **RNF-12** — Contraseñas hasheadas (`set_password`/`check_password` de
  Django), nunca texto plano; conexión a Neon vía `sslmode=require`.

## Pruebas realizadas (evidencia)

- Registro de usuario vía `POST /api/registro` → usuario creado con rol
  `CLIENTE` en Neon (verificado en tabla `usuarios_usuario`).
- Login vía `POST /api/login` → JWT válido devuelto.
- `GET /api/usuarios/me` sin token → `401 Authentication credentials were not
  provided`.
- `GET /api/usuarios/me` con token → datos del usuario autenticado.
- `GET /api/usuarios` con token de rol `CLIENTE` → `403 Forbidden` (confirma
  separación de roles real en backend).

## Pendiente / próximos pasos

- CRUD de contenidos administrables (`Contenido`) y temas visuales (`Tema`).
- Endpoint de mensajes de contacto (`MensajeContacto`).
- Importación masiva de usuarios vía CSV (RF12).
- Conexión del frontend (React) a estos endpoints.
- Despliegue remoto del servicio.

## Primer administrador

Se crea de forma segura mediante `python manage.py createsuperuser`
(password solicitado de forma interactiva, nunca hardcodeado en el código ni
en el repositorio).