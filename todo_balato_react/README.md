# React conectado a Django: versión sencilla

Esta copia de trabajo mantiene intacta la aplicación original `todo-balato` y la
copia anterior `todo-balato-integracion`.

## Alcance

- Registro e inicio/cierre de sesión usan los endpoints existentes de Gestión.
- React mantiene el token solo en memoria; al recargar la página se inicia una
  sesión nueva.
- El carrito permanece en React y Comercio calcula precio y disponibilidad.
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
| Crear orden pendiente | Comercio `POST /api/checkout` |

El registro envía nombre y apellido por separado. Checkout envía el token JWT y
la cabecera `Idempotency-Key`.

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

Abre `http://localhost:5173`. No guardes credenciales Django en el frontend.

## Próximas tareas

- Implementar el carrito persistente y la combinación del carrito anónimo al
  iniciar sesión.
- Persistir/renovar la sesión después de recargar.
- Integrar el pago sandbox cuando el backend esté preparado.
