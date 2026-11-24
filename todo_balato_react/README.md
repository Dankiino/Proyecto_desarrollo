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
  productos. Inicio muestra las categorías activas y hasta cuatro productos
  disponibles (`disponible=true`), junto con los textos, el banner y el tema
  activo obtenidos desde Gestión.
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
| Contenidos de Inicio | Gestión `GET /api/contenidos/inicio` |
| Tema activo del sitio | Gestión `GET /api/temas/activo` |
| Listar categorías activas | Catálogo `GET /api/categorias` |
| Listar productos activos | Catálogo `GET /api/productos?page=1&page_size=20` |
| Destacados disponibles de Inicio | Catálogo `GET /api/productos?page=1&page_size=4&disponible=true` |
| Detalle de producto activo | Catálogo `GET /api/productos/<producto_id>` |
| Calcular carrito | Comercio `POST /api/carrito/calcular` |
| Combinar carrito al iniciar sesión | Comercio `POST /api/carrito/combinar` |
| Guardar o cambiar cantidad | Comercio `PUT /api/carrito/items/<producto_id>` |
| Quitar producto | Comercio `DELETE /api/carrito/items/<producto_id>` |
| Consultar carrito guardado | Comercio `GET /api/carrito` (disponible en la API; la pantalla del carrito usa el cálculo de precios y existencias) |
| Crear orden pendiente | Comercio `POST /api/checkout` |

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

## Página de Inicio (Catálogo y Gestión)

La vista [Home.jsx](src/pages/Home.jsx) conserva el diseño, la navegación y las
tarjetas existentes (`ProductCard`), y consulta dos servicios:

- **Catálogo (`VITE_CATALOGO_API_URL`):**
  - `GET /api/categorias` para mostrar las categorías activas (cada botón navega
    a Catálogo filtrado por esa categoría).
  - `GET /api/productos?page=1&page_size=4&disponible=true` para mostrar hasta
    cuatro productos disponibles (con botones *Ver detalle* y *Agregar al Carrito*).
- **Gestión (`VITE_GESTION_API_URL`):**
  - `GET /api/contenidos/inicio` para obtener los textos administrables
    (`titulo`, `eslogan`, `titulo_categorias`, `titulo_destacados`) y el banner
    (`banner_principal` con `texto_alternativo` y `banner_enlace`).
  - `GET /api/temas/activo` (cargado desde `App.jsx`) para aplicar los colores
    del tema activo (`color_primario`, `color_secundario`, `color_fondo`,
    `color_texto`, `color_acento`) mediante variables CSS.

Cada bloque (contenidos/tema, categorías y productos destacados) maneja de forma
independiente su estado de carga, error con botón **Reintentar** y estado vacío,
sin presentar un fallo o un formato inválido como si fuera una respuesta exitosa.

### Cómo probar Inicio

1. **Con servicios reales:** levanta Gestión (`8000`), Comercio (`8001`) y
   Catálogo (`8002`), configura `.env.local` desde `.env.example` e inicia Vite
   (`npm run dev -- --strictPort`).
2. **Con respuestas de prueba (sin esperar a Gestión/DEA-35 o sin backend):**
   define `VITE_INICIO_MOCK` en `.env.local` o agrega `?mockInicio=<modo>` en la
   URL del navegador (`http://localhost:5173/?mockInicio=exito`). Modos disponibles:
   - `exito` (o `true`): simula Catálogo y Gestión con 4 productos disponibles,
     categorías, banner y tema `balato-crema`.
   - `gestion`: consulta **Catálogo real** y simula solo los contenidos y tema de
     Gestión mientras se termina `DEA-35`.
   - `tema_oscuro` / `tema_clasico`: prueba el cambio de tema dinámico.
   - `vacio`: verifica los mensajes cuando no hay contenidos, categorías ni
     productos disponibles.
   - `error`, `error_catalogo`, `error_gestion`: verifica los mensajes de error y
     el botón **Reintentar** ante caída de uno o ambos servicios.
3. **Comprobaciones recomendadas:**
   - Hacer clic en una categoría y comprobar que abre Catálogo con ese filtro.
   - Hacer clic en el banner, en *Ver detalle* y en *Agregar al Carrito*.
   - Revisar en escritorio y móvil (por ejemplo `360px` y `1280px`) y recorrer
     toda la página usando solo teclado (`Tab`, `Shift+Tab` y `Enter`).

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

Abre `http://localhost:5173`. No guardes credenciales Django en el frontend.

## Próximas tareas

- Persistir/renovar la sesión después de recargar.
- Integrar el pago sandbox cuando el backend esté preparado.
