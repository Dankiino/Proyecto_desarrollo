# Investigación de Arquitectura de Microservicios - Proyecto "Todo Balato"

## 1. Contexto y Enfoque Arquitectónico
Para el desarrollo de la plataforma de comercio electrónico "Todo Balato", se ha descartado la arquitectura monolítica tradicional. El requerimiento técnico establece estrictamente que un único proceso de Django con varias aplicaciones no demuestra una arquitectura de microservicios. 
Por lo tanto, la solución se estructurará basándose en procesos ejecutables y desplegables por separado, con responsabilidades claramente delimitadas, APIs documentadas y configuraciones independientes. Esto asegura que los fallos entre servicios sean aislados y observables.

## 2. Desglose de Microservicios y Propiedad de Datos
El backend operará mediante tres microservicios independientes. Cada uno será responsable de un dominio específico del negocio y tendrá propiedad exclusiva sobre sus datos, prohibiendo las consultas directas a tablas o colecciones ajenas:
*   **Servicio de Gestión (Identity & CMS):**
    *   **Responsabilidad:** Administración de identidad, usuarios, roles, contenidos, temas y contacto.
    *   **Tecnología y Persistencia:** Django + DRF operando sobre PostgreSQL.
*   **Servicio de Catálogo e Inventario:**
    *   **Responsabilidad:** Gestión de productos, referencias de imágenes, existencias, reservas y movimientos.
    *   **Tecnología y Persistencia:** Django + DRF operando sobre MongoDB. Se utilizará este motor para aprovechar operaciones atómicas y transacciones multidocumento en el manejo del stock.
*   **Servicio de Comercio (Checkout & Orders):**
    *   **Responsabilidad:** Administración del carrito autenticado, órdenes, pagos, conciliación y notificaciones.
    *   **Tecnología y Persistencia:** Django + DRF operando sobre PostgreSQL. Se utilizará la infraestructura compartida con el Servicio de Gestión, pero aislando los datos mediante un esquema o base separada con credenciales propias.

## 3. Patrones de Comunicación
*   **Cliente-Servidor:** React con Vite consumirá las APIs documentadas de cada servicio.
*   **Comunicación Inter-servicios:** La interacción entre dominios (ej. validar stock para una reserva) se realizará exclusivamente a través de llamadas HTTP/REST.

## 4. Viabilidad de Despliegue en la Nube
Para cumplir con la comprobación de cuotas, HTTPS y persistencia, se proyecta:
*   **Bases de Datos:** MongoDB Atlas para el inventario y Supabase/Render para alojar PostgreSQL.
*   **Backend y Frontend:** Evaluación de plataformas gratuitas compatibles como Vercel o Render, verificando el manejo de variables de entorno (secretos) y CORS.