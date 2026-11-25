# React conectado a Django: versión sencilla

Esta copia de trabajo mantiene intacta la aplicación original `todo-balato` y la
copia anterior `todo-balato-integracion`.

## Alcance

- Registro e inicio/cierre de sesión usan los endpoints existentes de Gestión.
- React mantiene el token solo en memoria; al recargar la página se inicia una
  sesión nueva.
- El carrito de quien no ha iniciado sesión (carrito anónimo) se guarda en el
  navegador y sobrevive a recargar la página. Con sesión iniciada, el carrito
  se guarda en Comercio. En ambos casos Comercio calcula precio y disponibilidad.
- Comercio recibe el pedido autenticado y lo crea como pendiente de pago. Esta
  versión no procesa pagos ni pide datos de tarjeta.
- Inicio, catálogo y detalle consultan el servicio público de Catálogo; React no
  se conecta directamente a MongoDB ni usa el fixture local como fuente de
  productos.
- La disponibilidad se muestra en las tarjetas y los productos agotados no se
  pueden agregar al carrito. Comercio vuelve a validar precio y stock.

## Enfoque inspirado en los tutoriales

Los tutoriales muestran la ruta, la vista, el modelo y el formulario de Django;
no enseñan a conectar React ni DRF. Como esta interfaz es React, el formulario
manda datos JSON a las vistas REST que ya existen. El puente es
`src/services/django.js`, con llamadas `fetch` pequeñas y explícitas. No se
agregan librerías HTTP, contextos globales, renovación automática de tokens ni
una arquitectura extra.

Revisa el flujo en `src/pages/AuthPage.jsx` y `src/services/django.js`; las rutas
del servidor están en `usuarios/urls.py` de Gestión y `ordenes/urls.py` de
Comercio. Django devuelve JSON porque el cliente de esta aplicación es React,
no una plantilla Django.

## Rutas usadas

| Acción | Ruta |
|---|---|
| Registrar | Gestión `POST /api/registro` |
| Login | Gestión `POST /api/login` |
| Consultar usuario | Gestión `GET /api/usuarios/me` |
| Logout | Gestión `POST /api/logout` |
| Listar categorías activas | Catálogo `GET /api/categorias` |
| Listar productos activos | Catálogo `GET /api/productos?page=1&page_size=20` |
| Detalle de producto activo | Catálogo `GET /api/productos/<producto_id>` |
| Calcular carrito | Comercio `POST /api/carrito/calcular` |
| Combinar carrito al iniciar sesión | Comercio `POST /api/carrito/combinar` |
| Guardar o cambiar cantidad | Comercio `PUT /api/carrito/items/<producto_id>` |
| Quitar producto | Comercio `DELETE /api/carrito/items/<producto_id>` |
| Consultar carrito guardado | Comercio `GET /api/carrito` (disponible en la API; la pantalla del carrito usa el cálculo de precios y existencias) |
| Crear orden pendiente | Comercio `POST /api/checkout` |
| Consultar contenidos y tema público | Gestión `GET /api/contenidos` |
| Consultar/editar contenidos (admin) | Gestión `GET/PATCH /api/admin/contenidos` |
| Cambiar tema activo (admin) | Gestión `PUT /api/admin/tema-activo` |

El registro envía nombre y apellido por separado. Checkout envía el token JWT y
la cabecera `Idempotency-Key`.

## Carrito guardado y carrito anónimo

**Sin sesión (carrito anónimo).** El carrito se guarda en el navegador, en
`localStorage`, bajo la clave `todo_balato_carrito_anonimo`. Solo contiene el
identificador de cada producto y su cantidad (por ejemplo
`[{"id":"prod_0001","cantidad":2}]`); precios y stock se consultan siempre a
Comercio. Si el navegador bloquea el almacenamiento, el carrito sigue
funcionando en memoria, pero se pierde al recargar.

**Al iniciar sesión.** React envía el carrito anónimo a Comercio
(`POST /api/carrito/combinar`) y el resultado pasa a ser el carrito de la
pantalla. Después borra el carrito anónimo del navegador, para que no vuelva a
mezclarse en otro inicio de sesión. Si la combinación falla (por ejemplo,
Comercio apagado), el inicio de sesión muestra el error y el carrito anónimo no
se pierde.

**Regla de combinación.** Si un producto está en ambos carritos, queda la
**mayor** cantidad (no se suman). Con 2 unidades en el carrito anónimo y 3 en la
cuenta, quedan 3. Un producto que está en un solo carrito se agrega tal cual.
Combinar varias veces da siempre el mismo resultado, así que no se crean líneas
duplicadas. La regla completa está en el README de Comercio.

**Con sesión iniciada.** Agregar, cambiar cantidad y quitar productos se guarda
en Comercio (`PUT` y `DELETE` sobre `/api/carrito/items/<producto_id>`). El
carrito de una cuenta nunca se guarda en el navegador. Al cerrar sesión se vacía
el carrito de la pantalla, para que la siguiente persona que use el computador
no lo vea.

**Recuperar el carrito.** Como el token se mantiene solo en memoria, al recargar
la página con sesión iniciada hay que volver a iniciar sesión; al hacerlo, el
carrito de la cuenta se recupera desde Comercio. Si no había sesión, el carrito
anónimo se recupera del navegador. Al confirmar un pedido, el carrito guardado
en Comercio se vacía.

**Avisos.** La pantalla del carrito indica, en cada producto, si ya no existe,
está inactivo, está agotado o no tiene stock suficiente para la cantidad
elegida, y mantiene bloqueado el botón de pago hasta corregirlo.

### Contrato público del catálogo

Las rutas de Catálogo son públicas y no requieren una cuenta. El listado acepta
`page` (desde 1) y `page_size` (por defecto 20, máximo 50), además de `categoria`,
`precio_min`, `precio_max`, `disponible=true` y `orden`. Un tamaño fuera del
rango responde `400`.

El listado responde con `count`, `page`, `page_size` y `results`. Cada producto
incluye `id`, `nombre`, `imagen_principal` (objeto o `null`), `precio`, `moneda`,
`disponible` y `categorias`. El detalle agrega `descripcion`, `imagenes`
(incluido `texto_alternativo`), `stock_disponible` y `actualizado_en`.
Un producto inactivo o inexistente responde `404`.

Inicio y catálogo muestran carga, errores con opción de reintento y mensajes
cuando no hay resultados. Las tarjetas muestran “Agotado” y deshabilitan la
acción de agregar cuando `disponible` es `false`.

## Ejecutar en Windows

Inicia Catálogo en `127.0.0.1:8002`, Gestión en `127.0.0.1:8000` y Comercio
en `127.0.0.1:8001`, cada uno con su `.env` local. Para cambiar la dirección
del catálogo, configura `VITE_CATALOGO_API_URL` en el entorno de Vite (por
ejemplo, `http://127.0.0.1:8002/api`). Luego, desde CMD en esta carpeta:

```cmd
copy .env.example .env.local
npm ci
npm run dev -- --strictPort
```

## Administración de contenidos y temas (DEA-35)

- **Ruta de administración:** `/admin` (por ejemplo `http://127.0.0.1:5173/admin`),
  separada de la navegación pública.
- **Acceso:** inicia sesión con el correo y contraseña de una cuenta con rol
  `ADMIN` y estado `ACTIVO` (creada con `python manage.py createsuperuser` en
  Gestión).
- **Campos editables:**
  - **Inicio:** título principal, eslogan, título de categorías, título de
    destacados, banner principal (URL/ruta y texto alternativo) y enlace del banner.
  - **Contacto:** título, introducción, correo, teléfono y horario.
  - **Quiénes somos:** título, texto principal e imagen (URL/ruta y texto alternativo).
- **Selección de tema:** permite elegir entre los 4 temas aprobados
  (`balato-clasico`, `balato-crema`, `balato-oscuro`, `balato-contraste`). Las
  páginas públicas leen el tema desde Gestión al cargar y aplican sus colores
  mediante variables CSS (`--tema-*` y `data-tema`).
- **Errores y persistencia:** los errores de validación de Django se muestran
  debajo de cada campo sin sobrescribir los valores válidos guardados. Para
  comprobar persistencia, guarda un cambio, reinicia Gestión y recarga la página
  pública.

## Registro de recorrido público y administración (entorno real)

Los siguientes casos son verificaciones manuales de aceptación; React consulta
los servicios reales configurados en `VITE_CATALOGO_API_URL`, Catálogo,
Gestión y Comercio, no el fixture `src/data/mockCatalogo.json`. El código fuente
y los contratos describen esos recorridos, pero no se encontró en este
repositorio una captura, salida de navegador o registro fechado que demuestre
cada recorrido de extremo a extremo. Por ello, no se marca aquí como resultado
ejecutado lo que solo está descrito por la implementación. No se repitieron
pruebas al actualizar este README.

| Caso | Resultado esperado / estado de evidencia | Evidencia que registrar al ejecutar |
|---|---|---|
| Catálogo paginado y filtro por categoría | La UI debe solicitar páginas y filtrar por categoría; el endpoint admite `page`, `page_size` y `categoria`. Sin resultado manual verificable adjunto. | URL consultada y captura de página 1 y página 2; respuesta de `GET /api/productos?page=1&page_size=20&categoria=<id>`. |
| Detalle y galería | El detalle activo debe mostrar imágenes y texto alternativo. Sin resultado manual verificable adjunto. | ID del producto de prueba, captura de la galería y respuesta de `GET /api/productos/<id>`. |
| Formulario de contacto | Gestión documenta respuesta `201` y almacenamiento del mensaje en PostgreSQL. Falta evidencia del recorrido React completo en este README. | Código `201` de `POST /api/contacto/` y comprobación del mensaje desde el panel de ADMIN. |
| Producto agotado o inactivo | Las tarjetas deben bloquear agregar cuando `disponible=false`; el contrato indica que el detalle inactivo responde `404`. Falta evidencia manual adjunta del intento de compra. | Captura del botón deshabilitado y respuesta de carrito/checkout al intentar operar con el producto. |
| `/admin` para ADMIN activo, CLIENTE, ADMIN bloqueado y sin sesión | La protección debe validarse en la UI y en Django; ocultar o bloquear la pantalla no sustituye las respuestas `401/403` de la API. Sin registro de prueba de UI adjunto. | Capturas por rol y códigos de `GET/PATCH /api/admin/contenidos` y `PUT /api/admin/tema-activo`. |
| Edición de contenidos y tema, reinicio de Gestión | La secuencia de persistencia está descrita arriba; falta registrar valores y evidencia antes/después de reiniciar. | Valor anterior/nuevo, tema seleccionado y consulta `GET /api/contenidos` tras el reinicio. |

### Comprobaciones locales reproducibles

Desde esta carpeta, los siguientes comandos verifican calidad del cliente y
generan el frontend, pero **no** son pruebas de integración con los servicios:

```cmd
npm run lint
npm run build
```

Para el recorrido real, iniciar React en `http://127.0.0.1:5173` y los servicios
en los puertos indicados en «Ejecutar en Windows», con sus conexiones reales
configuradas en archivos `.env` locales. No incluir esos secretos en capturas,
comandos guardados ni documentación versionada.

