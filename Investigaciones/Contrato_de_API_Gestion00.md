# Contrato de API: Gestión (cuentas y sesión)

Proyecto de comercio electrónico · Solemne 02 · Backend · Versión 0.1 (propuesta) · 21-11-2026

## Propósito

Este documento define cómo el frontend (React) usa el servicio de Gestión para registrar clientes, activar cuentas, iniciar y cerrar sesión, recuperar contraseñas y bloquear usuarios. Cubre RF-07 a RF-10, RF-14 y RF-15, y la verificación de sesión que hace Comercio. Usa las convenciones comunes del documento "Contratos de API: convenciones y Catálogo", salvo lo indicado en "Diferencias con las convenciones". Todo lo marcado como propuesta debe ser aprobado por el equipo.

Los endpoints y las respuestas de este documento se comprobaron contra el servicio real (rama `Jean`, commit `2cd4711`, 21-11-2026). Los ejemplos son respuestas reales, salvo los valores que cambian en cada llamada (identificadores, fechas y tokens).

## Convenciones de Gestión

| Tema | Regla |
| --- | --- |
| URL base | Variable de entorno del frontend con la URL de Gestión (ver "Diferencias con las convenciones"). Local: `http://127.0.0.1:8000/api` |
| Autenticación | JWT emitido por Gestión. Se envía `Authorization: Bearer ACCESS` en los endpoints protegidos. El `access` dura 2 horas y el `refresh`, 1 día. Todavía no existe un endpoint para renovar el `access`: al vencer, la persona inicia sesión de nuevo |
| Roles | `CLIENTE` y `ADMIN`. El registro público solo crea clientes |
| Estados de cuenta | `PENDIENTE` (no activó su cuenta), `ACTIVO` y `BLOQUEADO`. Solo una cuenta `ACTIVO` inicia sesión y opera |
| Campos | `nombre`, `apellido`, `correo`, `password`. Identificadores: texto (UUID). Fechas: ISO 8601 en UTC (`2026-11-22T01:19:08.239047Z`) |
| Enlaces de correo | `FRONTEND_URL/activar?token=...` y `FRONTEND_URL/restablecer-password?token=...`. Vencen (24 h y 1 h) y sirven una sola vez. El frontend lee el token de la URL y lo envía a la API |

### Formato de errores

Gestión usa hoy el formato por defecto de Django REST Framework, que tiene tres formas:

```json
{ "detail": "Credenciales inválidas" }
```

```json
{ "correo": ["Enter a valid email address."], "password": ["This field is required."] }
```

```json
{ "detail": "Given token not valid for any token type", "code": "token_not_valid", "messages": [] }
```

La primera aparece en errores que no son de un campo. La segunda aparece en errores de validación: cada clave es el campo afectado y su valor es una lista de mensajes (CC-03). La tercera aparece cuando el token de sesión es inválido o venció. Para decidir qué mostrar, el frontend debe usar el código HTTP y el nombre de los campos, no el texto: los mensajes que genera Django o DRF salen en inglés, y los escritos por el equipo, en español.

| HTTP | Cuándo |
| --- | --- |
| 200, 201 | Operación realizada |
| 205 | Sesión cerrada (sin cuerpo) |
| 400 | Datos inválidos, enlace inválido o regla de negocio incumplida |
| 401 | Credenciales inválidas, falta el token, el token es inválido o la cuenta ya no está activa |
| 403 | Cuenta pendiente o bloqueada al iniciar sesión, o rol incorrecto |
| 404 | Usuario inexistente |
| 429 | Se superó el límite de solicitudes por hora |
| 503 | Lo devuelve Comercio cuando no puede verificar la sesión con Gestión |

## Resumen de endpoints

| Endpoint | Quién | Para qué |
| --- | --- | --- |
| POST /api/registro | Visitante | Crear una cuenta cliente pendiente y enviar el enlace de activación (RF-07) |
| POST /api/activar | Visitante | Activar la cuenta con el enlace del correo |
| POST /api/activar/reenviar | Visitante | Pedir un enlace de activación nuevo |
| POST /api/recuperar-password | Visitante | Pedir el enlace para cambiar una contraseña olvidada |
| POST /api/restablecer-password | Visitante | Cambiar la contraseña con el enlace |
| POST /api/login | Cliente, administrador | Iniciar sesión (RF-08) |
| POST /api/logout | Cliente, administrador | Cerrar sesión (RF-09) |
| GET /api/usuarios/me | Cliente, administrador | Consultar la cuenta de la sesión |
| GET /api/usuarios | Administrador activo | Listar usuarios |
| POST /api/usuarios/{id}/bloquear | Administrador activo | Bloquear un usuario (RF-14) |
| POST /api/usuarios/{id}/desbloquear | Administrador activo | Desbloquear un usuario (RF-15) |

## Activación de cuentas

Flujo que debe implementar el frontend:

1. La persona completa el registro y el frontend llama a `POST /api/registro`. La respuesta **no trae tokens**: la cuenta queda `PENDIENTE` y el frontend muestra "Revisa tu correo para activar tu cuenta".
2. El correo trae un enlace a `/activar?token=...` en el frontend. Esa página lee el token y llama a `POST /api/activar`.
3. Si responde 200, el frontend lleva a iniciar sesión. Si responde 400, muestra que el enlace no sirve y ofrece pedir uno nuevo con `POST /api/activar/reenviar`.
4. Si alguien intenta iniciar sesión antes de activar, `POST /api/login` responde 403.

### POST /api/registro

Público. Crea un cliente en estado `PENDIENTE` y envía el correo de activación.

Cuerpo:

```json
{ "nombre": "Ana", "apellido": "Perez", "correo": "ana@example.com", "password": "Clave-Segura-2026!x" }
```

| Campo | Regla |
| --- | --- |
| nombre, apellido | Texto obligatorio |
| correo | Correo válido y no registrado |
| password | Obligatoria, de 8 a 128 caracteres, que no sea común, no sea solo numérica y no se parezca al nombre, apellido o correo |

Respuesta 201:

```json
{ "id": "ee214f26-5e7e-443a-8755-7f14681bdcce", "nombre": "Ana", "apellido": "Perez", "correo": "ana@example.com" }
```

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 400 | Falta un campo | `{"nombre": ["This field is required."], ...}` |
| 400 | Correo inválido | `{"correo": ["Enter a valid email address."]}` |
| 400 | Correo ya registrado | `{"correo": ["usuario with this correo already exists."]}` |
| 400 | Contraseña no válida | `{"password": ["This password is too common.", "This password is entirely numeric."]}` |

- Si el cuerpo trae `rol` o `estado`, se ignoran: siempre se crea un `CLIENTE` `PENDIENTE`.
- Un error de validación no crea cuenta. Un fallo al enviar el correo no impide el registro: la cuenta queda creada y la persona puede pedir otro enlace con `activar/reenviar`.
- Un correo duplicado se rechaza con 400 (RF-07), por lo que este endpoint sí revela que el correo existe. Los demás endpoints de este documento no lo revelan.

### POST /api/activar

Público. Activa la cuenta con el token del enlace.

Cuerpo: `{ "token": "..." }`

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Enlace válido y cuenta `PENDIENTE` | `{"detail": "Cuenta activada."}` |
| 400 | Enlace alterado, vencido, ya usado, o cuenta que no está pendiente (por ejemplo, bloqueada) | `{"detail": "El enlace es inválido, venció o ya fue usado."}` |
| 400 | Falta `token` | `{"token": ["This field is required."]}` |

Los casos de enlace inválido devuelven el mismo mensaje a propósito, para que no se pueda averiguar la causa.

### POST /api/activar/reenviar

Público. Envía un enlace de activación nuevo y deja sin efecto el anterior.

Cuerpo: `{ "correo": "ana@example.com" }`

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Siempre que el correo tenga formato válido | `{"detail": "Si el correo corresponde a una cuenta elegible, enviaremos un enlace."}` |
| 400 | Correo con formato inválido | `{"correo": ["Enter a valid email address."]}` |
| 429 | Más de 5 solicitudes por hora desde la misma IP | Ver "Límite de solicitudes" |

La respuesta 200 es idéntica exista o no el correo, y esté la cuenta pendiente, activa o bloqueada. El correo solo se envía si la cuenta existe y está `PENDIENTE`. El frontend no debe prometer que el correo llegará: debe decir "Si el correo está registrado, recibirás un enlace".

## Recuperación de contraseña

1. En "Olvidé mi contraseña", el frontend llama a `POST /api/recuperar-password` con el correo y muestra siempre el mismo mensaje.
2. El correo trae un enlace a `/restablecer-password?token=...` en el frontend. Esa página pide la contraseña nueva y llama a `POST /api/restablecer-password`.
3. Si responde 400 con `password`, el frontend muestra los errores y deja reintentar con el mismo enlace.

### POST /api/recuperar-password

Público. Envía el enlace de cambio de contraseña (vigencia de 1 hora, un solo uso). Un enlace nuevo deja sin efecto el anterior.

Cuerpo: `{ "correo": "ana@example.com" }`

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Siempre que el correo tenga formato válido | `{"detail": "Si el correo corresponde a una cuenta elegible, enviaremos un enlace."}` |
| 400 | Correo con formato inválido | `{"correo": ["Enter a valid email address."]}` |
| 429 | Más de 5 solicitudes por hora desde la misma IP | Ver "Límite de solicitudes" |

La respuesta es idéntica exista o no el correo. El correo solo se envía a cuentas `ACTIVO`; una cuenta pendiente o bloqueada no recibe nada.

### POST /api/restablecer-password

Público. Cambia la contraseña con el token del enlace.

Cuerpo: `{ "token": "...", "password": "Otra-Clave-2026!y" }`. La contraseña sigue las mismas reglas que en el registro.

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Enlace válido y contraseña válida | `{"detail": "Contraseña actualizada."}` |
| 400 | Enlace alterado, vencido, ya usado, de otro tipo, o cuenta no activa | `{"detail": "El enlace es inválido, venció o ya fue usado."}` |
| 400 | Contraseña no válida. **El enlace no se consume** | `{"password": ["This password is too common."]}` |
| 400 | Falta `token` o `password` | `{"password": ["This field is required."]}` |

Al cambiar la contraseña se cierran las sesiones abiertas (los `refresh` quedan revocados). Un `access` ya emitido sigue sirviendo hasta que venza (máximo 2 horas).

### Límite de solicitudes

`POST /api/activar/reenviar` y `POST /api/recuperar-password` aceptan 5 solicitudes por hora **por IP**, con un contador aparte para cada endpoint. Cuentan todas las solicitudes, también las rechazadas con 400. Al superarlo responde:

```
HTTP 429
Retry-After: 3598
{ "detail": "Request was throttled. Expected available in 3598 seconds." }
```

`Retry-After` indica los segundos que faltan. El frontend debe mostrar su propio mensaje, por ejemplo "Hiciste demasiados intentos. Vuelve a intentarlo más tarde", y no el texto de `detail`.

## Sesión

### POST /api/login

Público.

Cuerpo: `{ "correo": "ana@example.com", "password": "..." }`

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Credenciales válidas y cuenta `ACTIVO` | `{"access": "...", "refresh": "...", "rol": "CLIENTE"}` |
| 401 | Credenciales inválidas (también si el correo no existe o el cuerpo viene vacío) | `{"detail": "Credenciales inválidas"}` |
| 403 | Credenciales válidas, pero la cuenta está `PENDIENTE` o `BLOQUEADO` | `{"detail": "Cuenta no activa"}` |

- El 403 solo aparece si la contraseña es correcta, así que no revela si un correo existe.
- El `rol` de la respuesta sirve para dirigir al administrador al espacio administrativo y al cliente a la tienda. Las operaciones protegidas verifican el rol en el backend (RF-10).
- La respuesta 403 no distingue entre pendiente y bloqueado (ver decisiones abiertas).

### POST /api/logout

Requiere sesión. Revoca el `refresh`.

Cuerpo: `{ "refresh": "..." }`

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 205 | Sesión cerrada | Sin cuerpo |
| 400 | `refresh` ausente, inválido o ya revocado | Sin cuerpo |
| 401 | Sin `access` válido | `{"detail": "Authentication credentials were not provided."}` |

### GET /api/usuarios/me

Requiere sesión. Devuelve la cuenta del `access` enviado, con el estado vigente.

Respuesta 200:

```json
{
  "id": "ee214f26-5e7e-443a-8755-7f14681bdcce",
  "nombre": "Ana",
  "apellido": "Perez",
  "correo": "ana@example.com",
  "rol": "CLIENTE",
  "estado": "ACTIVO",
  "creado_en": "2026-11-22T01:19:08.239047Z"
}
```

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 401 | Sin token | `{"detail": "Authentication credentials were not provided."}` |
| 401 | Token inválido o vencido | `{"detail": "Given token not valid for any token type", "code": "token_not_valid", "messages": [...]}` |
| 401 | Cuenta que ya no está activa (por ejemplo, bloqueada después de iniciar sesión) | `{"detail": "Cuenta no activa"}` |

Gestión consulta el estado real de la cuenta en cada solicitud: un `access` emitido antes de un bloqueo deja de servir de inmediato. Ante un 401, el frontend debe descartar la sesión y llevar a iniciar sesión.

## Administración de usuarios

Estos endpoints exigen un administrador activo. Con un cliente responden 403 `{"detail": "You do not have permission to perform this action."}`, y sin token, 401.

### GET /api/usuarios

Respuesta 200: lista simple (sin paginar ni envoltorio `results`) de objetos con `id`, `nombre`, `apellido`, `correo`, `rol`, `estado` y `creado_en`, con la misma forma de `GET /api/usuarios/me`.

### POST /api/usuarios/{id}/bloquear

Sin cuerpo (se envía `{}`). `{id}` es el identificador del usuario.

| HTTP | Cuándo | Cuerpo |
| --- | --- | --- |
| 200 | Usuario bloqueado | El usuario, con `"estado": "BLOQUEADO"` |
| 400 | El administrador intenta bloquearse a sí mismo | `{"detail": "No puedes bloquearte a ti mismo"}` |
| 400 | Es el último administrador activo | `{"detail": "No se puede bloquear al último administrador activo"}` |
| 404 | El usuario no existe | `{"detail": "Usuario no encontrado"}` |

Efecto del bloqueo: el usuario no puede iniciar sesión (403), su `access` anterior responde 401 y sus `refresh` quedan revocados. Sus órdenes e historial se conservan.

### POST /api/usuarios/{id}/desbloquear

Sin cuerpo. Respuestas: 200 con el usuario en `"estado": "ACTIVO"`, y 404 `{"detail": "Usuario no encontrado"}`. Hoy deja la cuenta `ACTIVO` aunque estuviera `PENDIENTE` antes del bloqueo; RF-15 pide que siga pendiente (ver decisiones abiertas).

## Verificación de sesión desde Comercio

Comercio no confía en el rol ni en el estado que trae el token. En cada solicitud autenticada llama a `GET /api/usuarios/me` de Gestión con el mismo `Authorization` y usa el `rol` y el `estado` de esa respuesta:

| Gestión responde | Comercio responde |
| --- | --- |
| 200 con cuenta `ACTIVO` | Continúa y valida el rol (`EsClienteActivo`: un administrador no compra) |
| 401 | 401. Una cuenta bloqueada o pendiente no compra aunque conserve un token anterior |
| No responde o falla | 503 `{"detail": "No se pudo verificar la sesión."}`. No se asume que la cuenta sigue activa |

## Diferencias con las convenciones

El documento de convenciones fija `{"error": {"codigo", "mensaje", "campos"}}` como formato de errores y Comercio lo cumple. Gestión se diferencia en esto, y hay que resolverlo:

| Tema | Convenciones | Gestión hoy |
| --- | --- | --- |
| Formato de errores | `{"error": {"codigo", "mensaje", "campos"}}` | Formato de DRF (ver arriba). `django.js` ya entiende ambos formatos |
| Variable con la URL de Gestión | `VITE_API_GESTION_URL` | El código del frontend lee `VITE_GESTION_API_URL` |
| Nombre de campo | `snake_case` en español | `password` está en inglés |
| Idioma de mensajes | Español | Los de Django y DRF salen en inglés (`LANGUAGE_CODE = 'en-us'`) |
| Listas | Paginadas (`page`, `page_size`, `results`) | `GET /api/usuarios` devuelve una lista sin paginar |

## Fuera de esta versión

- Contenidos, temas y mensajes de contacto (RF-02 a RF-06).
- Crear usuarios individualmente, importar por CSV y editar usuarios (RF-11 a RF-13).
- Un endpoint para renovar el `access` con el `refresh`.

## Decisiones abiertas para el equipo

- Formato de errores de Gestión: documentar el de DRF como está (propuesta, sin cambios de código) o unificarlo con el de las convenciones mediante un manejador de excepciones.
- Si la respuesta 403 de `login` incluye el estado (`PENDIENTE` o `BLOQUEADO`). Con él, el frontend mostraría "Reenviar enlace de activación" solo a las cuentas pendientes.
- Si se cambia `LANGUAGE_CODE` a español para que los mensajes de validación salgan en español.
- Si `GET /api/usuarios` se pagina según las convenciones.
- Si `/desbloquear` debe respetar el estado `PENDIENTE` previo (RF-15).
- Si se agrega el endpoint de renovación del `access` y cuándo.
- Nombre de la variable de entorno con la URL de Gestión (`VITE_API_GESTION_URL` o `VITE_GESTION_API_URL`).
