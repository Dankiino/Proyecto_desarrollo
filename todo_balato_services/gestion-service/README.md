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

Gestión necesita `GESTION_DATABASE_URL` y `JWT_SIGNING_KEY`; para enviar correos
reales, además las variables `EMAIL_*`, `DEFAULT_FROM_EMAIL` y `FRONTEND_URL`
(ver [Configuración del correo](#configuración-del-correo)). Comercio necesita
`COMERCIO_DATABASE_URL`, `CATALOGO_MONGO_URI`, la misma `JWT_SIGNING_KEY` y
`GESTION_URL`.
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
| POST | `/api/registro` | público | Crea usuario `PENDIENTE`, **siempre** rol `CLIENTE` (ignora cualquier `rol` enviado en el body), y envía el enlace de activación |
| POST | `/api/activar` | público | Activa la cuenta con el enlace del correo (temporal, un solo uso) |
| POST | `/api/activar/reenviar` | público | Envía un nuevo enlace de activación |
| POST | `/api/recuperar-password` | público | Envía el enlace para cambiar una contraseña olvidada (respuesta idéntica exista o no el correo) |
| POST | `/api/restablecer-password` | público | Cambia la contraseña con el enlace del correo (temporal, un solo uso) |
| POST | `/api/login` | público | Devuelve `access` + `refresh` JWT. Rechaza si `estado != ACTIVO` |
| POST | `/api/logout` | autenticado | Invalida (blacklist) el refresh token |
| GET | `/api/usuarios/me` | autenticado | Datos del usuario autenticado |
| GET | `/api/usuarios` | solo ADMIN activo | Lista todos los usuarios |
| POST | `/api/usuarios/:id/bloquear` | solo ADMIN activo | Bloquea un usuario |
| POST | `/api/usuarios/:id/desbloquear` | solo ADMIN activo | Reactiva un usuario |

## Reglas de negocio implementadas

- **RF07** — El registro público nunca crea administradores: el serializer ignora
  cualquier campo `rol` recibido y fuerza `CLIENTE` en estado `PENDIENTE`.
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

## Carga inicial de contenidos y temas

Carga en PostgreSQL de Gestión los cuatro temas visuales y los contenidos de
Inicio, Contacto y Quiénes somos. **No toca MongoDB**: categorías y productos
pertenecen al servicio de Catálogo y no se crean ni modifican aquí.

Con el entorno activo y las migraciones aplicadas (`python manage.py migrate`):

```powershell
python manage.py cargar_datos_iniciales
```

El comando imprime cuántos registros creó y cuántos ya existían. Los datos
están definidos en `contenidos/datos_iniciales.py`.

### Datos incluidos

| Tabla | Registros |
|---|---|
| `contenidos_tema` | `balato-clasico` (activo por defecto), `balato-crema`, `balato-oscuro`, `balato-contraste` |
| `contenidos_contenidopagina` | `inicio`: titulo, eslogan, titulo_categorias, titulo_destacados, banner_principal, banner_enlace |
| | `contacto`: titulo, introduccion, correo |
| | `quienes-somos`: titulo, texto, imagen |

### Repetir el proceso

Se puede ejecutar cuantas veces se quiera. Cada tema se identifica por su `id`
y cada contenido por `(pagina, clave)`; solo se crea lo que falta. Un registro
existente **nunca se modifica**, así que los cambios hechos por el administrador
se conservan. Solo se marca un tema como activo si no hay ninguno activo al
crearlo. Si se borra un registro, la siguiente ejecución lo vuelve a crear con su
valor inicial.

### Verificar los datos

```powershell
python manage.py shell -c "from contenidos.models import *; print(Tema.objects.count(), ContenidoPagina.objects.count(), list(Tema.objects.filter(activo=True).values_list('id', flat=True)))"
```

Resultado esperado tras la primera carga: `4 12 ['balato-clasico']`. También se
pueden revisar en `http://127.0.0.1:8000/admin/` (Contenidos → Temas y
Contenido páginas).

Para comprobar que no duplica ni sobrescribe:

1. Ejecuta `python manage.py cargar_datos_iniciales` dos veces: la segunda debe
   informar `0 creados` y el comando de verificación debe seguir mostrando `4 12`.
2. Cambia un valor desde el admin (por ejemplo `inicio.titulo`), vuelve a ejecutar
   la carga y confirma que conserva el cambio.
3. Prueba automática: `python manage.py test contenidos`.

## Activación de cuentas y recuperación de contraseña

Las cuentas nuevas nacen `PENDIENTE` y solo operan después de usar el enlace
enviado por correo. Una contraseña olvidada se cambia con otro enlace. Ambos
enlaces son temporales y sirven una sola vez.

### Flujo

| Paso | Endpoint | Resultado |
|---|---|---|
| Registro | `POST /api/registro` | Crea el cliente `PENDIENTE` y envía el enlace de activación |
| Activar | `POST /api/activar` `{token}` | `PENDIENTE` → `ACTIVO`. Un enlace inválido, alterado, vencido o ya usado responde `400` con el mismo mensaje |
| Reenviar activación | `POST /api/activar/reenviar` `{correo}` | Envía un enlace nuevo si la cuenta está `PENDIENTE`; el anterior deja de servir |
| Olvidé mi contraseña | `POST /api/recuperar-password` `{correo}` | Envía el enlace si la cuenta está `ACTIVO` |
| Nueva contraseña | `POST /api/restablecer-password` `{token, password}` | Cambia la contraseña con el enlace |

El enlace del correo es `FRONTEND_URL/activar?token=...` o
`FRONTEND_URL/restablecer-password?token=...`; el frontend lee el token y lo
envía a la API.

### Reglas de seguridad

- **Token**: 256 bits aleatorios (`secrets.token_urlsafe`). En la base solo se
  guarda su hash SHA-256 (tabla `usuarios_tokencuenta`), nunca el token.
- **Vigencia**: activación 24 h, recuperación 1 h (`TOKEN_VIGENCIA` en
  `settings.py`).
- **Un solo uso**: el token se marca como usado con un `UPDATE` condicional
  (`usado_en IS NULL` y no vencido) dentro de la misma transacción que el cambio
  de estado o de contraseña, así que dos solicitudes simultáneas no lo usan dos
  veces. Pedir un enlace nuevo invalida el anterior.
- **No revela correos**: `activar/reenviar` y `recuperar-password` responden lo
  mismo exista o no el correo, y sea cual sea el estado de la cuenta (`200` con
  un mensaje genérico). Solo se envía correo cuando corresponde.
- **Contraseña**: se valida en el servidor con `AUTH_PASSWORD_VALIDATORS` (largo
  mínimo, máximo 128 caracteres, comunes, numéricas y parecidas al nombre, apellido o correo) y se
  guarda solo su hash. Si la contraseña no pasa, responde `400` por campo y el
  enlace **no** se consume. Al cambiarla se cierran las sesiones (refresh tokens)
  existentes.
- **Estados**: una cuenta `PENDIENTE` o `BLOQUEADA` no inicia sesión (`403`). Un
  enlace de activación no activa una cuenta bloqueada y un enlace de recuperación
  no cambia la contraseña de una cuenta que no esté `ACTIVO`.
- **Bloqueo inmediato**: Gestión consulta el estado real de la cuenta en cada
  solicitud (`usuarios/authentication.py`), por lo que un access token emitido
  antes del bloqueo recibe `401`; además, al bloquear se revocan sus refresh
  tokens. Comercio no confía en el estado guardado dentro del token: consulta
  `GET /api/usuarios/me` a Gestión (`GESTION_URL`) en cada solicitud autenticada,
  de modo que una cuenta bloqueada tampoco puede comprar. Si Gestión no responde,
  Comercio rechaza con `503`.
- **Fallos de correo**: se registran en el log (sin el token ni el contenido del
  correo) y no interrumpen la operación; la persona puede pedir un enlace nuevo.

### Configuración del correo

`settings.py` arma `MAILERS` (la API vigente de Django 6.1; `EMAIL_BACKEND`, `EMAIL_HOST`,
etc. como *settings* de Django están deprecados) a partir de las variables de entorno de
abajo. Por defecto (`EMAIL_BACKEND` sin definir) los correos se imprimen en la consola
del servidor, sin enviar nada. Para el envío real, agrega en tu `gestion-service\.env`
local las variables `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` y `FRONTEND_URL` (nombres en
`.env.example`). Los valores reales los entrega el equipo por un canal seguro:
**no se guardan en el repositorio, en `.env.example` ni en capturas o chats**.
Para producción, configúralas como variables de entorno de la plataforma.

### Cómo probar

**Pruebas automáticas** (no envían correos reales ni necesitan SMTP):

```powershell
python manage.py test usuarios
```

Cubren: cuenta pendiente al registrarse y envío del enlace; solo se guarda el
hash del token y de la contraseña; activación válida; enlaces **vencidos,
alterados, repetidos** y de otro propósito; reenvío que invalida el enlace
anterior; respuesta idéntica para **correos no registrados**, pendientes y
bloqueados; contraseña débil sin consumir el enlace; cuenta **bloqueada** que no
activa ni restablece; token de sesión anterior al bloqueo rechazado; y un fallo
de correo que no rompe el registro. Las pruebas de Comercio:
`python manage.py test ordenes`.

**Prueba manual.** Usa dos ventanas de PowerShell, **ambas dentro de
`gestion-service`** y con el entorno virtual activado (`.\venv\Scripts\Activate.ps1`):

- **Ventana 1 (servidor)**: `python manage.py runserver 127.0.0.1:8000`. Déjala
  corriendo; los correos se imprimen aquí. Para el paso D necesitas un
  administrador (`python manage.py createsuperuser` si aún no existe).
- **Ventana 2 (pruebas)**: pega esto una sola vez. Define los atajos `post` y
  `get`, que muestran **siempre el código HTTP** seguido de la respuesta, tanto
  si sale bien como si falla.

```powershell
$api = "http://127.0.0.1:8000/api"
function req($metodo, $ruta, $cuerpo, $tk) {
  $h = @{}; if ($tk) { $h.Authorization = "Bearer $tk" }
  $p = @{ Method=$metodo; Uri="$api/$ruta"; Headers=$h; UseBasicParsing=$true }
  if ($null -ne $cuerpo) { $p.ContentType = "application/json"; $p.Body = ($cuerpo | ConvertTo-Json) }
  try { $r = Invoke-WebRequest @p; "$($r.StatusCode) $($r.Content)" }
  catch { "$($_.Exception.Response.StatusCode.value__) $($_.ErrorDetails.Message)" }
}
function post($ruta, $cuerpo, $tk) { req "POST" $ruta $cuerpo $tk }
function get($ruta, $tk) { req "GET" $ruta $null $tk }
```

**Comprueba que responde Gestión** (y no otro servicio en ese puerto, por ejemplo
Comercio):

```powershell
get "usuarios/me"     # 401 {"detail":"Authentication credentials were not provided."}
```

Cualquier otro resultado (`404`, error de conexión) indica que el puerto `8000`
no es Gestión: revisa que la ventana 1 siga corriendo y que la URL sea
`http://127.0.0.1:8000`.

**A. Activación de cuenta**

```powershell
post registro @{nombre="Ana"; apellido="Perez"; correo="ana@example.com"; password="Clave-Segura-2026!x"}   # 201
post login @{correo="ana@example.com"; password="Clave-Segura-2026!x"}                                    # 403 (pendiente)
```

Saca el token del correo que apareció en la ventana 1. La consola lo imprime
codificado (*quoted-printable*), por ejemplo:

```text
http://localhost:5173/activar?token=3DDqGi5SUpbah72RjEnUPOhf0ru5wYElctUgudP4I=
1FgE
```

- El token empieza **después de `token=3D`**: `=3D` es solo la codificación del `=`.
- Un `=` al final de la línea indica que el token continúa en la siguiente:
  quítalo y une las dos partes. En el ejemplo, el token es
  `DqGi5SUpbah72RjEnUPOhf0ru5wYElctUgudP4I1FgE`.

```powershell
$t1 = "pega-aquí-el-token"
post activar @{token=$t1}                  # 200 "Cuenta activada."
post activar @{token=$t1}                  # 400 (ya usado)
post activar @{token="${t1}x"}             # 400 (alterado)
post login @{correo="ana@example.com"; password="Clave-Segura-2026!x"}   # 200 con access y refresh
```

**B. Recuperación de contraseña**

```powershell
post recuperar-password @{correo="ana@example.com"}
post recuperar-password @{correo="nadie@example.com"}
```

Las dos respuestas deben ser idénticas (`200`). En la ventana 1 el correo debe
aparecer solo para `ana@`. Saca el nuevo token igual que en A.

```powershell
$t2 = "pega-aquí-el-token"
post restablecer-password @{token=$t2; password="12345678"}                # 400 (clave débil, el enlace sigue vigente)
post restablecer-password @{token=$t2; password="Otra-Clave-2026!y"}       # 200 "Contraseña actualizada."
post restablecer-password @{token=$t2; password="Otra-Clave-2026!z"}       # 400 (repetido)
post login @{correo="ana@example.com"; password="Clave-Segura-2026!x"}     # 401 (la clave vieja ya no sirve)
post login @{correo="ana@example.com"; password="Otra-Clave-2026!y"}       # 200
```

**C. Enlace vencido**

```powershell
post recuperar-password @{correo="ana@example.com"}
```

Este comando va **en la ventana 2, dentro de `gestion-service`** (necesita el
entorno virtual y el `.env` de Gestión):

```powershell
python manage.py shell -c "from usuarios.models import TokenCuenta; from django.utils import timezone; from datetime import timedelta; TokenCuenta.objects.update(vence_en=timezone.now()-timedelta(seconds=1))"
```

```powershell
$t3 = "token-del-nuevo-correo"
post restablecer-password @{token=$t3; password="Otra-Clave-2026!w"}      # 400
```

**D. Cuenta bloqueada**

Obtén el `access` de Ana, el del administrador y el id de Ana (reemplaza los
datos del administrador por los tuyos):

```powershell
$access = (Invoke-RestMethod -Method Post "$api/login" -ContentType "application/json" -Body (@{correo="ana@example.com"; password="Otra-Clave-2026!y"} | ConvertTo-Json)).access
$admin  = (Invoke-RestMethod -Method Post "$api/login" -ContentType "application/json" -Body (@{correo="TU-ADMIN@correo"; password="TU-CLAVE-ADMIN"} | ConvertTo-Json)).access
$id     = (Invoke-RestMethod "$api/usuarios/me" -Headers @{Authorization="Bearer $access"}).id
```

Bloquéala y comprueba que la sesión que ya tenía deja de funcionar:

```powershell
get "usuarios/me" $access                                                 # 200 (antes de bloquear)
post "usuarios/$id/bloquear" @{} $admin                                   # 200
get "usuarios/me" $access                                                 # 401 (el token previo ya no sirve)
post login @{correo="ana@example.com"; password="Otra-Clave-2026!y"}      # 403
```

**E. Envío real**: configura el SMTP en tu `.env` (ver arriba), reinicia Gestión,
registra una cuenta con un correo propio y comprueba que llegan los correos y que
los enlaces funcionan.

**Notas**

- **Límite de solicitudes**: `recuperar-password` acepta 5 por hora por IP. Esta
  guía usa 3, pero si la repites completa recibirás `429`. Reiniciar el servidor
  (ventana 1) reinicia el contador.
- **Base de datos real**: las pruebas crean a `ana@example.com` en la base de tu
  `.env`. Si es compartida con el equipo, bórrala al terminar (dentro de
  `gestion-service`):

  ```powershell
  python manage.py shell -c "from usuarios.models import Usuario; Usuario.objects.filter(correo='ana@example.com').delete()"
  ```

- Si el primer `post` da un error extraño (de conexión o TLS), confirma que la
  ventana 1 sigue corriendo y que la URL es `http://127.0.0.1:8000`.

### Limitaciones conocidas

- `POST /api/registro` con un correo ya registrado responde `400` (RF07 exige
  rechazar duplicados), por lo que ese endpoint sí permite saber si un correo
  existe. Recuperación y reenvío no lo revelan.
- El envío de correo es síncrono: quien consulta un correo registrado puede
  tardar algo más en recibir la respuesta. Un hilo o una cola lo evitaría, pero
  no es fiable en plataformas serverless.
- `recuperar-password` y `activar/reenviar` tienen un límite de 5 solicitudes por
  hora **por IP** (`ScopedRateThrottle`, respuesta `429`; ajustable en
  `DEFAULT_THROTTLE_RATES`). Usa la caché por defecto de Django (en memoria de cada
  proceso), así que con varios procesos o instancias el límite se cuenta por
  separado; en producción conviene una caché compartida (Redis). No limita por
  correo: varias IP distintas aún pueden escribirle a una misma bandeja.
- Desbloquear (`/desbloquear`) pone la cuenta en `ACTIVO` aunque estuviera
  `PENDIENTE` antes del bloqueo; RF-15 pide que siga pendiente.
- El frontend aún no tiene las rutas `/activar` y `/restablecer-password` ni el
  formulario de "olvidé mi contraseña".

## Pendiente / próximos pasos

- CRUD de contenidos administrables (`ContenidoPagina`) y temas visuales (`Tema`); la carga inicial ya existe.
- Endpoint de mensajes de contacto (`MensajeContacto`).
- Importación masiva de usuarios vía CSV (RF12).
- Conexión del frontend (React) a estos endpoints.
- Despliegue remoto del servicio.

## Primer administrador

Se crea de forma segura mediante `python manage.py createsuperuser`
(password solicitado de forma interactiva, nunca hardcodeado en el código ni
en el repositorio).