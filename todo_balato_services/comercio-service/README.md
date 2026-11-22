# Servicio de Comercio

Servicio Django responsable de las operaciones de carrito y checkout. Usa
PostgreSQL (`comercio_db`) y consulta productos en MongoDB Atlas
(`catalogo_db`).

## Configuración local en Windows

Desde CMD, ubicado en `comercio-service`:

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Si usas PowerShell y aparece un error indicando que la ejecución de scripts está
bloqueada, permite la activación solo en esa terminal y activa el entorno:

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

```cmd
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

La API local queda disponible bajo `http://127.0.0.1:8001/api/`.

Para desarrollo local, CORS permite los orígenes de Vite
`http://localhost:5173` y `http://127.0.0.1:5173`.

## Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/carrito/calcular` | Calcula el carrito con productos del catálogo |
| POST | `/api/checkout` | Procesa la solicitud de checkout autenticada |

El checkout requiere un JWT válido emitido por Gestión y la cabecera
`Idempotency-Key`. En cada solicitud autenticada, Comercio consulta a Gestión
(`GET /api/usuarios/me`) el rol y el estado vigentes: una cuenta bloqueada deja
de comprar aunque conserve un token emitido antes del bloqueo. Si Gestión no
responde, la solicitud se rechaza con 503 (no se asume que la cuenta sigue activa).
Consulta los contratos y validaciones del código antes de integrar un cliente.

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
  segura. Hasta entonces el inicio de pago responde 503 y no se puede completar una compra real.

### Pruebas

```cmd
python manage.py test ordenes
```

`ordenes/test_pagos.py` simula Webpay y el inventario: aprobación, rechazo, cancelación, respuesta alterada (monto y
orden), retorno repetido, Webpay sin respuesta con nueva revisión, doble clic, orden ajena y administrador.

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

### Limitaciones conocidas

- El inventario (`reservar`, `consolidar`, `liberar`) está pendiente de DEA-46. Hasta entonces el inicio de pago responde 503.
- Una transacción que Webpay aborta se detecta por el texto `aborted` del error (422) de `commit`. Es una suposición basada
  en el comportamiento observado en el sandbox, no una garantía documentada por Transbank.
- Una orden que queda en `PENDIENTE_PAGO` por un retorno que nunca llega mantiene su reserva hasta que exista el vencimiento
  de 15 minutos con liberación y la conciliación (RF-30, RF-38).
- Webpay Plus no devuelve moneda: solo se crean transacciones de órdenes en CLP.
