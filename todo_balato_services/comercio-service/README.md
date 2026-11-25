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

El cambio de política termina al cerrar esa terminal. En CMD, usa
`venv\Scripts\activate.bat` como en los comandos de configuración.

Completa `.env` con los valores privados del equipo:

- `COMERCIO_DATABASE_URL`: conexión PostgreSQL de Comercio.
- `CATALOGO_MONGO_URI`: conexión a MongoDB Atlas.
- `JWT_SIGNING_KEY`: debe ser exactamente la misma clave configurada en Gestión.
- `GESTION_URL`: URL base de Gestión (local: `http://127.0.0.1:8000`).
- `WEBPAY_COMMERCE_CODE`, `WEBPAY_API_KEY`: credenciales de sandbox de Webpay Plus (se piden al equipo por canal seguro).
- `WEBPAY_RETURN_URL`: URL de Comercio a la que Webpay devuelve al cliente (local: `http://127.0.0.1:8001/api/pagos/webpay/retorno`).
- `FRONTEND_RESULT_URL`: página de React a la que se redirige al cliente tras el pago.

No uses las credenciales de ejemplo como valores reales ni compartas el archivo
`.env`.

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

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/api/carrito/calcular` | público | Calcula el carrito (anónimo) con productos consultados a Catálogo |
| GET | `/api/carrito` | cliente activo | Consulta el carrito guardado, con precios, stock y avisos recalculados en Catálogo |
| PUT | `/api/carrito/items/<producto_id>` | cliente activo | Fija la cantidad de un producto en el carrito guardado (agrega si no estaba; con `0` lo quita) |
| DELETE | `/api/carrito/items/<producto_id>` | cliente activo | Quita un producto del carrito guardado |
| POST | `/api/carrito/combinar` | cliente activo | Combina el carrito anónimo con el carrito guardado de la cuenta |
| POST | `/api/checkout` | cliente activo | Procesa la solicitud de checkout autenticada |

El checkout requiere un JWT válido emitido por Gestión y la cabecera
`Idempotency-Key`. En cada solicitud autenticada, Comercio consulta a Gestión
(`GET /api/usuarios/me`) el rol y el estado vigentes: una cuenta bloqueada deja
de comprar aunque conserve un token emitido antes del bloqueo. Si Gestión no
responde, la solicitud se rechaza con 503 (no se asume que la cuenta sigue activa).
Solo se permite checkout a `CLIENTE` activo. El carrito debe tener al menos un
producto, cantidades enteras positivas y un solo renglón por producto. El total
se vuelve a calcular consultando Catálogo; si cambió frente a `total_esperado`,
se responde `409 precio_cambiado` con los precios y total vigentes. La misma
clave y el mismo pedido devuelven la orden original; reutilizarla con otro
pedido devuelve `409 conflicto`.

Antes de persistir la orden, checkout llama a `ordenes/inventario.py` para
reservar las líneas. Si la reserva falla, devuelve `503 inventario_no_disponible`
y no crea la orden. Mientras DEA-46 no implemente
Catálogo/inventario, ese adaptador falla de forma segura; los tests simulan
éxito y fallo de la reserva.

## Pago con Webpay Plus (ambiente de prueba)

El cliente siempre usa `IntegrationType.TEST`: no se cobra dinero real. Las credenciales y las URLs
salen solo de variables de entorno (nada en el repositorio ni en React). Comercio nunca pide ni guarda
números de tarjeta: el cliente los ingresa en el formulario de Webpay.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/pagos/iniciar` | Cliente dueño de la orden. Aparta el stock y crea la transacción; devuelve `url` y `token_ws` para redirigir a Webpay |
| GET/POST | `/api/pagos/webpay/retorno` | Webpay devuelve aquí al cliente. Comercio verifica con Webpay y redirige a `FRONTEND_RESULT_URL?orden=<id>` (sin token) |
| POST | `/api/pagos/<orden_id>/reverificar` | Cliente dueño. Vuelve a revisar un pago sin resultado o con confirmación pendiente |

Flujo y reglas (módulo `ordenes/pagos.py`):

- La orden se confirma (`CONFIRMADA`) solo si Webpay devuelve `AUTHORIZED` con `response_code` 0, el `buy_order` y el
  monto coinciden con la orden y Catálogo consolidó el stock. Si falta la consolidación queda en `CONFIRMACION_PENDIENTE`.
- Rechazo (`RECHAZADA`) o cancelación con `TBK_TOKEN` (`CANCELADA`): se guarda el estado y se libera el stock.
- Si Webpay autoriza pero el monto o la orden no coinciden: pago `INCONSISTENTE`, orden `REVISION_REQUERIDA`, sin confirmar.
- Retorno repetido: se bloquea el pago (`select_for_update`); un pago ya resuelto no repite el `commit` ni descuenta stock otra vez.
- Si Webpay no responde: pago `POR_VERIFICAR`, la orden no se muestra aprobada; `reverificar` consulta el estado antes de repetir el `commit`.
- `buy_order` es `"O"` + 25 caracteres del id de la orden (Webpay admite máximo 26). El token se guarda en `Pago.token_ws`
  y no se escribe en logs ni en respuestas públicas.
- Webpay Plus no devuelve moneda: solo se crean transacciones de órdenes en CLP.
- Pendiente (DEA-46): `ordenes/inventario.py` tiene `reservar`, `consolidar` y `liberar` como stubs que fallan de forma
  segura. Hasta entonces checkout y el inicio de pago responden 503 sin simular
  una reserva en producción y no se puede completar una compra real.

### Pruebas

```cmd
python manage.py test ordenes
```

`ordenes/test_pagos.py` simula Webpay y el inventario: aprobación, rechazo, cancelación, respuesta alterada (monto y
orden), retorno repetido, Webpay sin respuesta con nueva revisión, doble clic, orden ajena y administrador.
`ordenes/tests.py` cubre entradas inválidas y duplicadas, permisos, reintentos y
conflictos de idempotencia, precio actualizado, snapshot de líneas, falta de
stock, Catálogo no disponible y reserva simulada antes de persistir la orden.

### Pruebas manuales en sandbox (22-11-2026)

Credenciales de integración de Webpay Plus, tarjeta VISA de prueba y `inventario.py` con los stubs
reemplazados temporalmente por `return`.

| Caso | Resultado observado (orden / pago) |
|---|---|
| Aprobación | `CONFIRMADA` / `APROBADO` |
| Rechazo | `RECHAZADA` / `RECHAZADO` |
| Cancelación ("Anular compra") | `CANCELADA` / `CANCELADO` |
| Respuesta alterada (total modificado antes de pagar) | `REVISION_REQUERIDA` / `INCONSISTENTE` |
| Retorno repetido | Nada cambia |
| Webpay sin respuesta (API key falsa) | `PENDIENTE_PAGO` / `POR_VERIFICAR`, nunca aprobada. Webpay abortó la transacción antes del reintento (422 `aborted`) |

El caso "Webpay sin respuesta" se cubre además con pruebas automáticas (`test_pagos.py`).


