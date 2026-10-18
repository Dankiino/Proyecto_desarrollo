# Arquitectura de microservicios

Proyecto de comercio electrónico · Solemne 02 · Backend · 17-10-2026

## Resumen

El frontend en React (Vite) consume tres servicios Django independientes: Gestión, Catálogo y Comercio. Cada servicio es dueño de su propia base de datos (PostgreSQL o MongoDB) y ningún servicio consulta directamente las tablas o colecciones de otro. Comercio, además, usa Webpay Plus en ambiente de pruebas para los pagos.

## Servicios y bases de datos

| Servicio | Responsabilidad | Base de datos |
| --- | --- | --- |
| Gestión | Identidad, usuarios, roles, contenidos, temas y contacto | PostgreSQL (esquema de gestión) |
| Catálogo | Productos, imágenes, stock, reservas y movimientos | MongoDB |
| Comercio | Carrito autenticado, órdenes, pagos, conciliación y notificaciones | PostgreSQL (esquema o base separada, con credenciales propias) |
| Webpay Plus (externo) | Procesamiento de pagos en sandbox de Transbank | No aplica |

&#91;image: image.png\]

## Comunicación entre componentes

- **React hacia los tres servicios:** mediante API HTTPS con JSON.
- **Comercio hacia Catálogo:** consultar precios y stock al validar el checkout, reservar, consolidar y liberar. Cada una será un endpoint interno documentado en los contratos.
- **Comercio hacia Webpay:** crear la transacción, confirmarla con commit y consultar su estado con status.
- **Regla de propiedad de datos:** cada servicio usa solo su base. Si necesita datos de otro, los pide por su API.

## Lo que el diagrama no muestra

- **Llamadas internas:** la flecha de Comercio a Catálogo representa varias operaciones (precios, reserva, consolidación y liberación).
- **Redirección del cliente:** Webpay también redirige el navegador del cliente, no solo se comunica con Comercio. Ese flujo está en el diagrama de secuencia.
- **Autenticación:** el diagrama no indica cómo Catálogo y Comercio saben quién es el usuario. Si el equipo decide usar un JWT firmado por Gestión, cada servicio lo verifica por su cuenta y no se necesita otra flecha. Si cada petición consultara a Gestión, habría que añadirla.
- **Base de Comercio:** el enunciado permite una base separada o un esquema distinto dentro del PostgreSQL de Gestión, siempre con credenciales separadas.

## Pendiente para la versión final de H1

La rúbrica evalúa límites, datos, APIs, fallos y despliegue. Falta completar:

- **Despliegue:** dónde corre cada pieza (plataforma de cada servicio y MongoDB Atlas).
- **Fallos entre servicios:** qué pasa si un servicio cae. Por ejemplo, si Catálogo no responde, Comercio no confirma la compra y deja la orden en estado pendiente.
- **Decisiones abiertas con el equipo:** mecanismo de autenticación (JWT o sesiones) y URLs base de cada servicio.
