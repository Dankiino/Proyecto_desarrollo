# Contratos de API: convenciones y Catálogo

Proyecto de comercio electrónico · Solemne 02 · Backend · Versión 0.1 (propuesta) · 17-10-2026

## Propósito

Este documento define cómo se comunican el frontend (React) y el servicio de Catálogo, para que ambos equipos trabajen en paralelo. Cubre RF-20 (catálogo público) y RF-21 (detalle y galería). Todo lo marcado como propuesta debe ser aprobado por el equipo.

## Convenciones comunes (propuesta)

| Tema | Regla |
| --- | --- |
| Formato | JSON en UTF-8, con la cabecera Content-Type: application/json |
| URLs base | Un host por servicio, configurado en el frontend con variables de entorno: VITE\_API\_GESTION\_URL, VITE\_API\_CATALOGO\_URL y VITE\_API\_COMERCIO\_URL |
| Nombres de campos | snake\_case en español, como en el enunciado (stock\_fisico, descripcion) |
| Identificadores | Texto (string), únicos e inmutables |
| Dinero | Entero positivo en pesos chilenos, sin decimales, junto al campo moneda. Ejemplo: precio 15990 y moneda CLP. Nunca números decimales |
| Fechas | ISO 8601 en UTC. Ejemplo: 2026-10-17T14:30:00Z |
| Autenticación | Cabecera Authorization: Bearer TOKEN en los endpoints protegidos. Los públicos no la requieren. El mecanismo final queda pendiente del equipo (HU-03) |
| Paginación | Parámetros page (desde 1) y page\_size (por defecto 20, máximo 50). Un valor fuera de rango responde 400 |

### Formato de listas paginadas

```json
{
  "count": 57,
  "page": 1,
  "page_size": 20,
  "results": []
}
```

count es el total de elementos que cumplen la consulta, no los de la página.

### Formato de errores

```json
{
  "error": {
    "codigo": "validacion",
    "mensaje": "Los datos enviados no son válidos.",
    "campos": {
      "page_size": ["Debe ser un entero entre 1 y 50."]
    }
  }
}
```

El campo campos solo aparece en errores de validación e identifica cada campo afectado (CC-03). Los demás errores llevan solo codigo y mensaje, sin detalles internos.

| HTTP | codigo | Cuándo |
| --- | --- | --- |
| 400 | validacion | Parámetros o cuerpo inválidos |
| 401 | no\_autenticado | Falta la sesión o el token es inválido |
| 403 | no\_autorizado | Rol incorrecto o usuario bloqueado |
| 404 | no\_encontrado | Recurso inexistente (o inactivo, en endpoints públicos) |
| 409 | conflicto | Estado incompatible, por ejemplo una reserva existente con datos distintos |
| 500 | error\_interno | Fallo inesperado |
| 503 | servicio\_no\_disponible | Un servicio del que depende no responde |

## Catálogo público

Servicio: Catálogo e Inventario (MongoDB). No requiere autenticación y solo muestra productos activos.

### GET /api/productos

Lista paginada de productos.

Parámetros de consulta (todos opcionales): page, page\_size y los filtros descritos abajo.

Filtros y orden (propuesta):

| Parámetro | Valores | Notas |
| --- | --- | --- |
| categoria | Identificador de una categoría | Muestra los productos que tengan esa categoría entre las suyas |
| precio\_min | Entero en pesos | Incluye el valor indicado |
| precio\_max | Entero en pesos | Incluye el valor indicado. No puede ser menor que precio\_min |
| disponible | true | Solo productos con stock disponible. Sin el parámetro, también se listan los agotados |
| orden | recientes, precio\_asc, precio\_desc, nombre\_asc | Por defecto: recientes |

Reglas de los filtros:

- Los filtros y el orden se aplican antes de paginar. count es el total de productos que cumplen los filtros.
- Los filtros se combinan: un producto debe cumplir todos.
- Un valor inválido (por ejemplo, orden=cualquiera o un precio\_min mayor que precio\_max) responde 400 e indica el campo afectado en campos.
- Los productos inactivos siguen sin aparecer, con o sin filtros.

Ejemplo de consulta:

```
GET /api/productos?categoria=ropa&precio_min=5000&precio_max=20000&disponible=true&orden=precio_asc&page=1&page_size=20
```

Respuesta 200:

```json
{
  "count": 2,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": "6710f3a2c4b1e5a7d8f90123",
      "nombre": "Producto de ejemplo A",
      "imagen_principal": {
        "url": "https://cdn.example.com/productos/ejemplo-a-1.jpg",
        "texto_alternativo": "Producto de ejemplo A visto de frente"
      },
      "precio": 12990,
      "moneda": "CLP",
      "disponible": true,
      "categorias": [
        { "id": "ropa", "nombre": "Ropa" }
      ]
    },
    {
      "id": "6710f3a2c4b1e5a7d8f90124",
      "nombre": "Producto de ejemplo B",
      "imagen_principal": {
        "url": "https://cdn.example.com/productos/ejemplo-b-1.jpg",
        "texto_alternativo": "Producto de ejemplo B visto de frente"
      },
      "precio": 24990,
      "moneda": "CLP",
      "disponible": false,
      "categorias": [
        { "id": "ropa", "nombre": "Ropa" },
        { "id": "hogar", "nombre": "Hogar" }
      ]
    }
  ]
}
```

Reglas:

- Los productos inactivos nunca aparecen.
- disponible es false cuando el stock disponible (físico menos reservado) es cero. El frontend muestra el producto como agotado y no permite agregarlo al carrito.
- Si no hay productos, responde 200 con count 0 y results vacío. Si page supera el total de páginas, también responde 200 con results vacío y el count real (propuesta).
- Si page o page\_size son inválidos, responde 400 con el formato de errores.

### GET /api/productos/{id}

Detalle de un producto con su galería.

Respuesta 200:

```json
{
  "id": "6710f3a2c4b1e5a7d8f90123",
  "nombre": "Producto de ejemplo A",
  "descripcion": "Descripción completa del producto de ejemplo.",
  "precio": 12990,
  "moneda": "CLP",
  "disponible": true,
  "stock_disponible": 8,
  "categorias": [
    { "id": "ropa", "nombre": "Ropa" }
  ],
  "imagenes": [
    { "url": "https://cdn.example.com/productos/ejemplo-a-1.jpg", "texto_alternativo": "Vista frontal" },
    { "url": "https://cdn.example.com/productos/ejemplo-a-2.jpg", "texto_alternativo": "Vista lateral" },
    { "url": "https://cdn.example.com/productos/ejemplo-a-3.jpg", "texto_alternativo": "Vista posterior" },
    { "url": "https://cdn.example.com/productos/ejemplo-a-4.jpg", "texto_alternativo": "Detalle" }
  ],
  "actualizado_en": "2026-10-17T14:30:00Z"
}
```

Reglas:

- imagenes tiene entre 4 y 6 elementos (RB-05). La primera es la imagen principal.
- stock\_disponible es el stock físico menos el reservado y nunca es negativo. No se exponen el físico ni el reservado por separado.
- Un producto inexistente, inactivo o con identificador de formato inválido responde 404 con la misma respuesta, para no revelar información.

Respuesta 404:

```json
{
  "error": {
    "codigo": "no_encontrado",
    "mensaje": "El producto no existe o no está disponible."
  }
}
```

### GET /api/categorias

Lista de categorías para armar el filtro del catálogo. Es público y no usa paginación.

Respuesta 200:

```json
{
  "results": [
    { "id": "ropa", "nombre": "Ropa" },
    { "id": "hogar", "nombre": "Hogar" }
  ]
}
```

Reglas:

- Un producto puede tener varias categorías (supuesto actual). En las respuestas de productos aparecen en categorias, con id y nombre. La lista va vacía si el producto no tiene ninguna.
- Al filtrar por categoria, un producto aparece si tiene esa categoría entre las suyas.
- El id de una categoría es un texto estable, que no cambia aunque cambie el nombre.

## Cómo simular desde el día uno

El backend y el frontend se construyen al mismo tiempo, así que el frontend no puede esperar a que el servicio de Catálogo esté terminado. La solución es un mock: un servidor falso que responde con los JSON de este documento.

### Qué es un mock

Un mock es un programa pequeño que corre en el computador de quien hace el frontend y responde a las mismas URLs que el servicio real (por ejemplo, GET /api/productos), pero con datos fijos copiados de este contrato. Para React no hay diferencia: pide una URL y recibe un JSON con el formato acordado.

### Cómo usarlo (pasos para el equipo de frontend)

1. Elegir una herramienta. Las más simples son json-server (un archivo JSON y un comando) y Mockoon (aplicación con interfaz gráfica, sin escribir código). MSW intercepta las peticiones dentro del navegador y es más avanzada.
2. Copiar al mock los JSON de ejemplo de este documento, uno por cada endpoint.
3. Guardar la URL del servicio en una variable de entorno, en vez de escribirla dentro del código. En el archivo .env del frontend:

```
VITE_API_CATALOGO_URL=http://localhost:3001
```

4. Usar esa variable en todas las peticiones:

```javascript
const url = `${import.meta.env.VITE_API_CATALOGO_URL}/api/productos?page=1&page_size=20`;
const respuesta = await fetch(url);
const datos = await respuesta.json();
```

### Cuando el servicio real esté listo

Solo se cambia la línea del archivo .env. El código de React no se modifica:

```
VITE_API_CATALOGO_URL=https://catalogo.ejemplo.com
```

Esto funciona porque ambos lados siguen el mismo contrato.

### Acuerdos entre los equipos

- Backend devuelve exactamente los campos, nombres y tipos de este documento. Si precio pasara a llamarse price, el frontend dejaría de funcionar.
- Todo cambio al contrato se avisa antes y queda anotado en una nueva versión de este documento.
- Si el frontend necesita un dato que no está en el contrato, lo pide a backend para agregarlo al documento, en vez de inventarlo solo en el mock.
- El archivo .env no se sube al repositorio. Se sube un .env.example con los nombres de las variables y valores de ejemplo.

## Fuera de esta versión

- Endpoints administrativos del catálogo: crear, editar y desactivar productos y ajustar stock (RF-16 a RF-19).
- Endpoints internos de Comercio hacia Catálogo: validar precios y stock, reservar, consolidar y liberar. Se documentan junto con el contrato del Checkout.

## Decisiones abiertas para el equipo

- Mecanismo de autenticación: JWT o sesiones.
- URLs base de cada servicio desplegado.
- Si un page\_size mayor a 50 se rechaza con 400 (propuesta) o se recorta a 50.
- Si el público ve el número stock\_disponible o solo el booleano disponible.
- Qué responde GET /api/productos si page supera el total de páginas: 200 con results vacío (propuesta) o 404.
- Categorías por producto: se asume que un producto puede tener varias. Confirmar con el equipo.
- Quién administra las categorías y cómo se crean: el enunciado no las define y RF-16 no las incluye, así que habría que agregarlas al producto y a su formulario de creación y edición.
- Si el filtro categoria acepta una sola categoría (propuesta) o varias a la vez.
- Valores del parámetro orden y cuál es el orden por defecto.
