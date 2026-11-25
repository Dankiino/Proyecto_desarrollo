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
    └── views.py         # catálogo público y endpoints de salud
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
.
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

## Endpoints públicos del catálogo

Las rutas de lectura no requieren autenticación. `page` empieza en 1;
`page_size` es 20 por defecto y acepta valores de 1 a 50. Un valor fuera de
rango devuelve `400` con un error de validación.

### `GET /api/productos`

Lista solo productos activos. Parámetros opcionales:

| Parámetro | Uso |
|---|---|
| `page` | Página solicitada, desde 1 |
| `page_size` | Productos por página, entre 1 y 50 |
| `categoria` | Identificador de categoría |
| `precio_min`, `precio_max` | Rango inclusivo de precio |
| `disponible=true` | Filtra productos con stock disponible |
| `orden` | `recientes`, `precio_asc`, `precio_desc` o `nombre_asc` |

Respuesta `200`:

```json
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": "prod_0001",
      "nombre": "Set de vasos",
      "imagen_principal": {
        "url": "https://ejemplo.test/vasos.jpg",
        "texto_alternativo": "Set de vasos, vista frontal"
      },
      "precio": 3990,
      "moneda": "CLP",
      "disponible": true,
      "categorias": [{ "id": "cocina", "nombre": "Cocina" }]
    }
  ]
}
```

`imagen_principal` es `null` cuando MongoDB no tiene imágenes. Si no hay
coincidencias, responde `200` con `count: 0` y `results: []`. Los agotados
siguen apareciendo salvo que se solicite `disponible=true`; `disponible` se
calcula como stock físico menos reservado.

### `GET /api/categorias`

Devuelve categorías activas sin paginación:

```json
{ "results": [{ "id": "cocina", "nombre": "Cocina" }] }
```

### `GET /api/productos/<producto_id>`

Devuelve el producto activo con `descripcion`, `stock_disponible`,
`actualizado_en` y la galería `imagenes`, cuyos elementos tienen `url` y
`texto_alternativo`. La primera imagen también se devuelve como
`imagen_principal`. Un producto inexistente o inactivo responde `404`.

Los errores de conexión o acceso a MongoDB responden `503`; no se convierten en
listas vacías.

## Consumo desde React y `comercio-service`

- React consulta las rutas públicas de listado, categorías y detalle desde el
  navegador; no necesita una cuenta ni se conecta directamente a MongoDB.
- Inicio, catálogo y detalle muestran estados de carga y error; el catálogo
  también muestra el resultado vacío. Las tarjetas deshabilitan agregar cuando
  `disponible` es `false`.
- `comercio-service` consume el detalle por HTTP para validar sus operaciones.

- **Rutas de salud:**
  - `GET [http://127.0.0.1:8002/api/health](http://127.0.0.1:8002/api/health)` -> `{"status": "ok", "service": "catalogo-service"}`
  - `GET [http://127.0.0.1:8002/api/health/mongo](http://127.0.0.1:8002/api/health/mongo)` -> verifica lectura en MongoDB desde `catalogo-service`
- **Endpoint de lectura consumido por `comercio-service`:**
  - `GET {CATALOGO_API_URL}/productos/<producto_id>` (ejemplo local: `http://localhost:8002/api/productos/<producto_id>`)
  - En `comercio-service`, se configura mediante la variable de entorno `CATALOGO_API_URL` (ejemplo: `CATALOGO_API_URL=http://localhost:8002/api`, sin credenciales ni valores privados).
- **Comportamiento ante errores o falta de disponibilidad:** si un producto no existe (`404` / no encontrado), la respuesta es inválida o `catalogo-service` no está disponible, `comercio-service` lo maneja explícitamente (por ejemplo, marcando el ítem como `no_existe` con `puede_pagar: false` en `POST /api/carrito/calcular` o devolviendo `503 Service Unavailable` cuando Catálogo está caído) sin convertirlo en productos vacíos ni en falsos éxitos.

## Verificación sin acceso directo de Comercio a MongoDB

1. Confirma que `comercio-service` no tenga `pymongo` ni variables/conexiones de MongoDB y que `catalogo-service` sea el único servicio con acceso a MongoDB.
2. Inicia `catalogo-service` en `127.0.0.1:8002` y `comercio-service` en `127.0.0.1:8001` con `CATALOGO_API_URL=http://localhost:8002/api`.
3. Prueba `POST /api/carrito/calcular` (y `POST /api/checkout` cuando aplique) en `comercio-service` con un producto existente, uno inexistente (`200` con `problema: "no_existe"`) y con `catalogo-service` detenido (`503`), validando que la comunicación ocurre vía HTTP y que los errores se reportan de forma explícita sin acceso directo de Comercio a MongoDB.

## Ajustes manuales de inventario

El panel administrativo permite modificar el stock físico de un
producto y consultar el historial de ajustes realizados.

### Autenticación y permisos

Las operaciones requieren un token Bearer válido de Gestión.

Solo las cuentas con rol `ADMIN` y estado `ACTIVO` pueden realizar
ajustes o consultar el historial.

Los clientes, administradores bloqueados y usuarios sin una sesión
válida no tienen acceso a estas operaciones, incluso si realizan
solicitudes directamente al servicio de Catálogo.

La conexión con Gestión utiliza la variable `GESTION_API_URL`,
cuyo valor local predeterminado es `http://127.0.0.1:8000/api`.

### Registrar un ajuste de inventario

`POST /api/admin/productos/<producto_id>/ajustes`

Cabeceras:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Ejemplo de solicitud:

```json
{
  "stock_fisico": 70,
  "motivo": "Corrección por conteo físico"
}
```

Reglas de validación:

- El stock físico debe ser un número entero mayor o igual a cero.
- El valor máximo permitido es 2147483647.
- El stock físico no puede ser inferior al stock reservado.
- El motivo es obligatorio y admite hasta 500 caracteres.
- No se permite modificar el stock reservado mediante esta operación.
- La identidad del administrador se obtiene desde Gestión.
- El cliente no puede proporcionar ni modificar los datos de auditoría.

El stock físico y su historial se actualizan mediante una misma
operación atómica sobre el documento del producto en MongoDB.

### Consultar el historial de ajustes

`GET /api/admin/productos/<producto_id>/ajustes`

Devuelve el stock físico actual, el stock reservado, la cantidad
total de ajustes y el historial ordenado desde el registro más
reciente al más antiguo.

Cada ajuste almacena los siguientes campos:

| Campo | Descripción |
|---|---|
| ajuste_id | Identificador único del ajuste |
| producto_id | Identificador del producto |
| stock_anterior | Stock físico antes del ajuste |
| stock_nuevo | Stock físico después del ajuste |
| motivo | Justificación del cambio |
| administrador_id | Identificador del administrador |
| administrador_nombre | Nombre y apellido del administrador |
| administrador_correo | Correo del administrador |
| fecha | Fecha y hora del ajuste en UTC |

El historial se almacena en el campo `historial_ajustes` del
documento del producto en MongoDB.

### Códigos de respuesta

| Código | Descripción |
|---|---|
| 200 | Historial consultado correctamente |
| 201 | Ajuste registrado correctamente |
| 400 | Datos de solicitud inválidos |
| 401 / 403 | Sesión inválida o acceso no autorizado |
| 404 | Producto inexistente |
| 409 | Ajuste incompatible con las condiciones del inventario |
| 503 | Servicio de Gestión o MongoDB no disponible |

### Protección de la edición general

El endpoint `PATCH /api/admin/productos/<producto_id>` no permite
modificar los campos `stock_fisico`, `stock_reservado` ni
`historial_ajustes`.

El stock físico inicial se establece durante la creación del
producto. Los cambios posteriores deben realizarse mediante
el endpoint específico de ajustes de inventario.

### Uso desde el panel administrativo de React

1. Iniciar sesión con una cuenta ADMIN activa.
2. Ingresar a la sección de productos.
3. Seleccionar el botón "Ajustar inventario".
4. Revisar el stock físico, reservado y disponible.
5. Ingresar el nuevo stock físico y el motivo del cambio.
6. Guardar el ajuste.
7. Consultar el historial mostrado en el mismo panel.

### Pruebas automatizadas

Desde el directorio `catalogo-service`, ejecutar:

```bash
python manage.py test productos -v 2
```

Se incorporaron 14 pruebas automatizadas de inventario que cubren:

- Validación de cantidades y motivos.
- Protección de campos de auditoría.
- Permisos de acceso.
- Ajustes válidos.
- Conflictos con unidades reservadas.
- Consulta y orden del historial.
- Protección de la edición general.
- Estructura de la actualización atómica en MongoDB.

Resultado de la suite completa: 27 pruebas aprobadas.

### Dependencias y validaciones pendientes

La implementación reutiliza la conexión de Catálogo con MongoDB
(DEA-31) y la validación de administradores de DEA-33.

El almacenamiento del historial dentro del documento del producto
debe revisarse con las validaciones e índices definidos en DEA-32.

Las pruebas automatizadas utilizan objetos simulados. Queda
pendiente la validación formal de integración con MongoDB y la
coordinación con las operaciones de reserva de Comercio (DEA-46).
### Validacion de compatibilidad con DEA-32

Pruebas realizadas el 24/11/2026.

- Se inspeccionaron los validadores e indices de la coleccion productos.
- La validacion de MongoDB es estricta y rechaza documentos invalidos.
- Los 14 productos existentes cumplen el esquema vigente.
- El esquema permite almacenar el campo historial_ajustes.
- El indice _id permite localizar eficientemente el producto.
- Se verifico la persistencia del ajuste de 50 a 70 unidades y su auditoria administrativa.

### Pruebas de integracion con MongoDB 8.0

Se utilizo Docker con una base local catalogo_test,
en el puerto 27018, replicando el validador vigente.

Resultados:

- 27 de 27 pruebas automatizadas aprobadas.
- Ajuste valido de 50 a 80 unidades: aprobado.
- Conservacion de las 10 unidades reservadas: aprobado.
- Incremento de version y registro del historial: aprobado.
- Rechazo de ajuste inferior al stock reservado: aprobado.
- Rechazo directo de MongoDB con codigo 121: aprobado.
- Conservacion del documento tras los intentos invalidos: aprobado.

No se modificaron los validadores ni los indices de la
base compartida durante estas pruebas de compatibilidad.

La compatibilidad con el esquema actual de DEA-32 queda
verificada. Los futuros cambios de esquema deben conservar
el soporte para historial_ajustes.

Queda pendiente la integracion con las operaciones de
reserva, consolidacion y liberacion de DEA-46.

---

## Revisión de validadores e índices en MongoDB (DEA-32)

Se inspeccionaron las colecciones existentes de `catalogo_db` en MongoDB Atlas
sin borrar ni recrear datos, comparándolas contra las reglas acordadas en
`Investigaciones/validaciones.md`.

### Estado encontrado

| Colección | Documentos | Validación | Índices existentes |
|---|---|---|---|
| `productos` | 14 | `$jsonSchema` + `$expr` (`strict` / `error`) | `_id_`, `activo_1_categoria_id_1` |
| `categorias` | 7 | `$jsonSchema` (`strict` / `error`) | `_id_` |

- **Validador de `productos`:** exige los 13 campos obligatorios (`_id`, `nombre`,
  `descripcion`, `precio`, `moneda`, `stock_fisico`, `stock_reservado`,
  `categoria_id`, `imagenes`, `activo`, `version`, `creado_en`, `actualizado_en`),
  `precio` entero `>= 1`, `moneda: "CLP"`, `stock_fisico` y `stock_reservado`
  enteros `>= 0`, entre 4 y 6 imágenes con `url` `^https?://` y `alt` no vacío,
  `version >= 1`, fechas tipo `date` y `$expr: { $lte: ["$stock_reservado", "$stock_fisico"] }`.
- **Validador de `categorias`:** exige `_id` con patrón `^[a-z0-9-]+$`, `nombre`
  entre 2 y 60 caracteres, `descripcion` opcional de máximo 200 caracteres,
  `orden` entero `>= 0` y `activa` booleano.

### Observaciones identificadas (sin modificar la base compartida)

- Los validadores e índices existentes cumplen las reglas acordadas en
  `Investigaciones/validaciones.md`, por lo que **no se aplicaron cambios**
  sobre las colecciones compartidas.
- **Mejoras opcionales documentadas para evaluar en equipo antes de tocar la base:**
  - En `productos`, `nombre`, `descripcion` y `imagenes[].alt` usan `minLength: 1`
    (no bloquean cadenas de solo espacios en MongoDB; hoy ese control lo hace Django).
  - La existencia de `categoria_id` se valida en Django, ya que MongoDB no tiene
    claves foráneas.
  - En `categorias`, un índice `{ activa: 1, orden: 1 }` puede acelerar el listado
    público ordenado si la colección crece.
  - Cualquier cambio futuro al validador de `productos` debe conservar soporte
    para el campo `historial_ajustes` usado por DEA-43.

### Script repetible de pruebas

El script [scripts/verificar_validaciones_mongo.py](./scripts/verificar_validaciones_mongo.py)
inspecciona las colecciones existentes y ejecuta 17 pruebas directamente contra
MongoDB (aceptación de documentos válidos y rechazo de inválidos con códigos
`121` y `11000`). Todos los documentos de prueba usan un prefijo temporal único
y se eliminan siempre en el bloque `finally`.

Ejecución desde `todo_balato_services/catalogo-service` (con `.env` configurado):

```powershell
.\venv\Scripts\python.exe scripts\verificar_validaciones_mongo.py
```

### Resultados de ejecución

- **Productos válidos aceptados (2/2):** producto con 4 imágenes y producto con 6 imágenes.
- **Productos inválidos rechazados (10/10):** precio `0`, precio decimal, moneda `USD`,
  stock físico negativo, stock reservado mayor al físico, 3 imágenes, 7 imágenes,
  imagen sin `alt`, URL `ftp://` (código `121`) y `_id` repetido (código `11000`).
- **Categorías (5/5):** categoría válida aceptada; rechazadas `_id` con mayúsculas/espacios,
  `nombre` de 1 carácter, `orden` negativo y `activa` no booleano (código `121`).
- **Integridad:** `17/17` pruebas aprobadas; se conservaron intactos los documentos
  existentes.
- **Carga adicional de catálogo:** se insertaron `22` productos nuevos
  (`prod_0013` a `prod_0034`, total `36` en `productos`) repartidos en las 6
  categorías activas, cada uno con 4 imágenes verificadas (HTTP 200) de Easy Chile
  y cumpliendo el validador estricto de MongoDB.

## Registro de pruebas de aceptación (admin y servicios reales)

Los resultados numéricos de la sección anterior corresponden a ejecuciones
previas registradas en este README. No se repitieron durante esta actualización.
La prueba del script sí se conecta directamente a la base MongoDB indicada por
`CATALOGO_MONGO_URI`; los tests Django habituales, en cambio, usan dobles
simulados para MongoDB y Gestión.

| Caso | Resultado registrado / estado | Evidencia / cómo repetir |
|---|---|---|
| Validadores de MongoDB | En la ejecución registrada: `17/17` aprobadas; 2 productos válidos aceptados, 10 productos inválidos rechazados, 5 casos de categorías aprobados/rechazados según regla. El total de documentos quedó igual antes/después de la limpieza. | `.\venv\Scripts\python.exe scripts\verificar_validaciones_mongo.py`; requiere `.env` con acceso real a Atlas. El script imprime códigos de rechazo y conteos de integridad, y elimina sus documentos temporales. |
| Producto con precio `0`, stock negativo o menos de 4 imágenes | Rechazados por MongoDB con código `121` en la ejecución registrada. También se probaron precio decimal, moneda USD, stock reservado superior al físico, 7 imágenes, imagen sin `alt` y URL `ftp://`. | Salida del script anterior: líneas `[OK] Rechazado (código 121)` y resultado final `17/17`. |
| Colecciones existentes y preservación de documentos | Inspección registrada: `productos` y `categorias` con validadores estrictos e índices; los documentos existentes se conservaron. La tabla de conteos del README corresponde a la inspección previa. | El script informa conteos e índices al inicio y compara los conteos luego de limpiar los temporales. |
| Permisos directos de ajustes de inventario | Tests Django documentan `401/403` para sin token, CLIENTE y ADMIN no activo, pero estos casos usan mocks para Gestión; no equivalen a llamadas en vivo entre servicios. | `python manage.py test productos -v 2`. Para integración real, usar `Invoke-WebRequest`/Postman contra `/api/admin/productos/<id>/ajustes` con perfiles reales de Gestión y registrar `401/403/201`. |
| Crear, editar y desactivar productos/categorías desde `/admin` | El repositorio documenta la verificación de validadores, pero no incluye resultados de evidencia UI para el CRUD completo ni una comparación antes/después de documentos existentes. | Pendiente de adjuntar captura y conteo de documentos antes/después para cada operación CRUD en el panel conectado a Atlas. |
| Integración de inventario contra MongoDB 8.0 local | Resultado previamente registrado con Docker y `catalogo_test`: ajuste válido, reservas conservadas, historial actualizado y operaciones inválidas rechazadas; los documentos se conservaron. Esta prueba local no es una prueba contra Atlas. | Resultados descritos en «Pruebas de integración con MongoDB 8.0»; no confundir con la validación del clúster Atlas. |

