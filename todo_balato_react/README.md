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
- Los productos son un fixture local con IDs compatibles con MongoDB. Catálogo
  aún no está conectado.

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
| Calcular carrito | Comercio `POST /api/carrito/calcular` |
| Crear orden pendiente | Comercio `POST /api/checkout` |

El registro envía nombre y apellido por separado. Checkout envía el token JWT y
la cabecera `Idempotency-Key`.

## Ejecutar en Windows

Inicia Gestión en `127.0.0.1:8000` y Comercio en `127.0.0.1:8001`, cada uno con
su `.env` local. Luego, desde CMD en esta carpeta:

```cmd
copy .env.example .env.local
npm ci
npm run dev -- --strictPort
```

Abre `http://localhost:5173`. No guardes credenciales Django en el frontend.

## Próximas tareas

- Cambiar el fixture por el futuro endpoint del servicio Catálogo.
- Implementar el carrito persistente y la combinación del carrito anónimo al
  iniciar sesión.
- Persistir/renovar la sesión después de recargar.
- Integrar el pago sandbox cuando el backend esté preparado.
