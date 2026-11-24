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

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/api/carrito/calcular` | público | Calcula el carrito (anónimo) con productos consultados a Catálogo |
| GET | `/api/carrito` | cliente activo | Consulta el carrito guardado, con precios, stock y avisos recalculados en Catálogo |
| PUT | `/api/carrito/items/<producto_id>` | cliente activo | Fija la cantidad de un producto en el carrito guardado (agrega si no estaba; con `0` lo quita) |
| DELETE | `/api/carrito/items/<producto_id>` | cliente activo | Quita un producto del carrito guardado |
| POST | `/api/carrito/combinar` | cliente activo | Combina el carrito anónimo con el carrito guardado de la cuenta |
| POST | `/api/checkout` | cliente activo | Procesa la solicitud de checkout autenticada |

El checkout requiere un JWT válido emitido por Gestión y la cabecera `Idempotency-Key`. Consulta los contratos y validaciones del código antes de integrar un cliente.

## Carrito guardado

El carrito guardado permite que un cliente recupere sus productos al recargar la página o al volver a iniciar sesión. Los modelos son `Carrito` (uno por cliente) y `LineaCarrito`, ambos en `ordenes/models.py`; los endpoints están en `ordenes/carrito_views.py`.

### Qué se guarda

Solo el identificador del producto (`producto_id`) y la cantidad. El precio, el nombre y el stock **no se guardan**: se vuelven a consultar a Catálogo cada vez que se pide el carrito (`GET /api/carrito`), así nunca quedan desactualizados.

### Quién puede usarlo y cómo se separan los datos

Todos los endpoints del carrito guardado exigen un JWT de Gestión con rol `CLIENTE` y estado `ACTIVO` (`Authorization: Bearer <access>`). El carrito se identifica con el `user_id` del token, por lo que cada cliente solo puede consultar y modificar el suyo; no existe ninguna ruta para acceder al carrito de otra persona. Sin sesión válida la API responde `401` o `403`.

### Cómo se evitan líneas duplicadas

`PUT /api/carrito/items/<producto_id>` recibe la cantidad **final**, no un incremento:

```json
{ "cantidad": 3 }
```

Repetir la misma petición siempre deja el mismo resultado. Además, la base de datos impide dos líneas del mismo producto en un carrito (`unique_together` sobre `carrito` y `producto_id`). La cantidad debe ser un entero entre `0` y `99` (`CANTIDAD_MAXIMA` en `carrito_views.py`); `0` quita el producto. Cualquier otro valor responde `400` con `codigo: "validacion"`.

Todos los endpoints que modifican el carrito responden con el contenido guardado:

```json
{ "items": [ { "producto_id": "prod_0001", "cantidad": 3 } ] }
```

### Regla de combinación del carrito anónimo y el de la cuenta

`POST /api/carrito/combinar` recibe el carrito anónimo (el que el cliente armó antes de iniciar sesión):

```json
{ "items": [ { "producto_id": "prod_0001", "cantidad": 2 } ] }
```

Reglas acordadas:

- **Producto en ambos carritos:** gana la **mayor cantidad**. Con 2 unidades en el carrito anónimo y 3 en el de la cuenta, quedan 3. Con 2 y 1, quedan 2.
- **Producto en un solo carrito:** se agrega tal cual.
- **Repetidos dentro del carrito anónimo:** también se usa la mayor cantidad.
- **No se suman las cantidades.** Combinar es idempotente: si la operación se repite (reintento, doble clic, recarga), el resultado es el mismo y no se crean líneas duplicadas.
- **La combinación no recorta cantidades por stock.** El stock se revisa al recuperar el carrito (ver más abajo).
- Cada item necesita un `producto_id` de texto y una cantidad válida mayor que 0; si no, responde `400` y no se guarda nada.

### Aviso de productos no disponibles al recuperar el carrito

`GET /api/carrito` devuelve las líneas recalculadas con Catálogo, el total, `puede_pagar` y la lista `avisos`:

```json
{
  "items": [ { "producto_id": "prod_0001", "cantidad": 20 } ],
  "moneda": "CLP",
  "lineas": [
    {
      "producto_id": "prod_0001",
      "nombre": "Set de 6 vasos de vidrio",
      "precio_unitario": 3990,
      "cantidad": 20,
      "subtotal": 0,
      "problema": "stock_insuficiente"
    }
  ],
  "total": 0,
  "puede_pagar": false,
  "avisos": [ { "producto_id": "prod_0001", "problema": "stock_insuficiente" } ]
}
```

Valores posibles de `problema`:

| Valor | Significado |
|---|---|
| `no_existe` | Catálogo no encuentra el producto |
| `inactivo` | El producto existe pero su estado no es `ACTIVO` |
| `agotado` | No hay stock disponible |
| `stock_insuficiente` | Hay stock, pero menos que la cantidad pedida |

Si hay al menos un producto con problema, `puede_pagar` es `false` y el checkout responde `409` hasta que se corrija el carrito. El carrito vacío responde `items: []`, `lineas: []` y `total: 0`.

Si Catálogo no responde, `GET /api/carrito` devuelve `503` (o `502` si la respuesta es inválida), pero el carrito guardado no se pierde.

### Pruebas

Con el entorno virtual activo, en `comercio-service`:

```bash
python manage.py test ordenes
```

Las pruebas (`ordenes/tests.py`) simulan Catálogo y cubren: agregar, cambiar cantidad y quitar productos; que repetir una operación no duplica líneas; cantidades inválidas; que solo se guarda identificador y cantidad; que precio y stock se consultan siempre en Catálogo; la combinación de carritos (mayor cantidad, idempotencia y datos inválidos); los avisos `no_existe`, `inactivo`, `agotado` y `stock_insuficiente`; la separación entre dos clientes; y el comportamiento cuando Catálogo no está disponible.