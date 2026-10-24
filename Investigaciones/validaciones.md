# Reglas de validación de Productos y Categorías

Una **validación** es una regla que los datos deben cumplir para ser aceptados. Por ejemplo: "el precio no puede ser negativo". Aquí están todas las reglas que el proyecto exige para los productos, explicadas en simple, para que quien programe sepa qué revisar y quien pruebe sepa qué intentar romper.

El proyecto además pide que, cuando algo esté mal, **el mensaje diga qué campo falló**, y que **nunca se muestre como exitoso algo que fue rechazado**.

---

## 1. Dónde se revisan los datos

Los datos se revisan en tres lugares, para que sea difícil que algo malo llegue a guardarse:

1. **En React (el formulario):** avisa rápido al usuario si se equivocó. Es solo una ayuda, porque cualquiera puede saltarse el formulario.
2. **En el servidor (Django):** es el filtro principal. Revisa todo lo que llega y responde con el error exacto. El proyecto exige que el servidor sea quien decida, no el navegador.
3. **En MongoDB:** es la última barrera. Aunque alguien intente escribir directo en la base, rechaza los datos incorrectos (ver sección 5).

---

## 2. Reglas del Producto

| Dato | Regla | Por qué | Mensaje de error sugerido |
|---|---|---|---|
| `id` | Único (no puede haber dos iguales) y **no se puede cambiar** después de creado | El proyecto lo exige | "El id ya existe" / el cambio se ignora o se rechaza |
| `nombre` | Texto obligatorio, no puede quedar vacío ni solo con espacios | El proyecto lo exige | "El nombre es obligatorio" |
| `descripcion` | Texto obligatorio, no puede quedar vacío | El proyecto lo exige | "La descripción es obligatoria" |
| `precio` | Número **entero mayor a 0** (en pesos) | El proyecto pide precio positivo; usamos enteros porque el peso no tiene decimales | "El precio debe ser mayor a 0" |
| `moneda` | Solo `"CLP"` | El proyecto indica que se usan pesos chilenos | "Moneda no permitida" |
| `stock_fisico` | Número **entero, 0 o más** (sin decimales ni negativos) | El proyecto lo exige | "El stock debe ser un entero mayor o igual a 0" |
| `stock_reservado` | Entero entre 0 y el stock físico. **No lo edita el administrador**: solo cambia con el proceso de compra (reservar, confirmar, liberar) | El proyecto indica que los campos de reservas no se asignan libremente desde el formulario | El campo se ignora o se rechaza si llega desde un formulario |
| `categoria_id` | Debe corresponder a una categoría que exista y esté activa | Decisión del equipo (el proyecto no menciona categorías) | "La categoría no existe" |
| `imagenes` | **Entre 4 y 6** imágenes (con 3 o con 7 se rechaza) | El proyecto lo exige | "Se requieren entre 4 y 6 imágenes" |
| `imagenes[].url` | Un enlace válido que empiece con http:// o https://, y que sea permanente | El proyecto pide referencias persistentes, no archivos temporales | "El enlace de la imagen no es válido" |
| `imagenes[].alt` | Texto descriptivo obligatorio | El proyecto pide texto alternativo para accesibilidad | "El texto alternativo es obligatorio" |
| `activo` | Solo verdadero o falso | El proyecto lo exige | "Estado inválido" |
| `version` | Número entero desde 1, que sube con cada edición. Si alguien edita con una versión vieja, se rechaza | El proyecto pide control de actualización | "El producto fue modificado por otra persona" |
| `creado_en` / `actualizado_en` | Las pone el servidor; el cliente no puede cambiarlas | El proyecto lo exige | No se aceptan desde el formulario |

---

## 3. Reglas de la tienda ligadas al producto

Además de revisar cada dato, hay reglas de cómo funciona la tienda:

- **Stock disponible = stock físico − stock reservado.** Nunca puede ser negativo.
- **Agotado:** un producto con stock físico en 0 se muestra como agotado y **no se puede agregar al carrito**.
- **Inactivo:** un producto con `activo: false` **no aparece en el catálogo público ni se puede comprar**, pero **no se borra**. Tampoco se puede agregar al carrito entrando directo por su dirección.
- **Ajuste de stock:**
  - el nuevo valor debe ser un entero de 0 o más;
  - **no puede quedar por debajo de lo que está reservado** (si hay 5 apartados, no se puede dejar el stock en 3);
  - debe quedar registrado quién lo hizo, cuándo y de qué valor a cuál (esto irá en la colección `movimientos_stock`).
- **Editar un producto no cambia las compras ya hechas.** Las órdenes copian el nombre y el precio del momento de la compra, así que si después se sube el precio, las compras antiguas conservan el valor que tenían.
- **El precio válido lo decide el servidor.** Aunque el navegador mande un precio, el servidor usa el que está en la base.
- **Productos por página:** como máximo 50 en cada respuesta del catálogo.

---

## 4. Reglas de la Categoría

| Dato | Regla | Mensaje de error sugerido |
|---|---|---|
| `id` (nombre corto) | Único; solo minúsculas, números y guiones; no cambia una vez creado | "Nombre corto inválido o repetido" |
| `nombre` | Texto obligatorio, entre 2 y 60 caracteres | "El nombre es obligatorio" |
| `descripcion` | Texto de máximo 200 caracteres | "Descripción demasiado larga" |
| `orden` | Número entero, 0 o más | "Orden inválido" |
| `activa` | Solo verdadero o falso | "Estado inválido" |

Una categoría que tenga productos asociados **no se borra**, solo se desactiva. Así ningún producto queda apuntando a una categoría que ya no existe.

---

## 5. La validación dentro de MongoDB

*Esta parte es para quien trabaje directamente con MongoDB. Quien no programe puede saltarla.*

MongoDB permite poner las reglas **en la propia colección**, de modo que rechace los datos incorrectos aunque lleguen por otro camino. Este código crea la colección `productos` con sus reglas:

```javascript
db.createCollection("productos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",

      // Campos que no pueden faltar
      required: ["_id", "nombre", "descripcion", "precio", "moneda",
                 "stock_fisico", "stock_reservado", "categoria_id",
                 "imagenes", "activo", "version", "creado_en", "actualizado_en"],

      properties: {
        _id:             { bsonType: "string" },
        nombre:          { bsonType: "string", minLength: 1 },       // no vacío
        descripcion:     { bsonType: "string", minLength: 1 },       // no vacía
        precio:          { bsonType: ["int", "long"], minimum: 1 },  // entero, mínimo 1
        moneda:          { enum: ["CLP"] },                          // solo CLP
        stock_fisico:    { bsonType: ["int", "long"], minimum: 0 },  // entero, 0 o más
        stock_reservado: { bsonType: ["int", "long"], minimum: 0 },
        categoria_id:    { bsonType: "string" },
        imagenes: {
          bsonType: "array", minItems: 4, maxItems: 6,               // de 4 a 6 fotos
          items: {
            bsonType: "object",
            required: ["url", "alt"],
            properties: {
              url: { bsonType: "string", pattern: "^https?://" },    // enlace http o https
              alt: { bsonType: "string", minLength: 1 }              // texto alternativo
            }
          }
        },
        activo:          { bsonType: "bool" },
        version:         { bsonType: ["int", "long"], minimum: 1 },
        creado_en:       { bsonType: "date" },
        actualizado_en:  { bsonType: "date" }
      }
    },

    // Regla que compara dos campos: lo reservado nunca supera al stock físico
    $expr: { $lte: ["$stock_reservado", "$stock_fisico"] }
  },
  validationLevel: "strict",   // revisa todas las escrituras
  validationAction: "error"    // rechaza lo que no cumpla
});

// Índice para acelerar el catálogo público filtrado por categoría
db.productos.createIndex({ activo: 1, categoria_id: 1 });
```

**Limitación a recordar:** MongoDB no puede comprobar que la categoría realmente exista, porque no tiene "claves foráneas" como las bases de datos de tablas. Esa comprobación la hace el servidor antes de guardar.

---

## 6. Pruebas para intentar romper las reglas

Cada una de estas pruebas debe ser **rechazada** (o ignorada) por el sistema. Si alguna se acepta, hay un error:

| Prueba | Resultado esperado |
|---|---|
| Crear un producto con precio `0`, negativo o con decimales | Rechazado |
| Crear un producto con stock negativo o con decimales | Rechazado |
| Crear un producto con 3 imágenes | Rechazado |
| Crear un producto con 7 imágenes | Rechazado |
| Crear un producto con 4 imágenes y otro con 6 | Aceptados |
| Una imagen sin texto alternativo | Rechazado |
| Un producto con stock reservado mayor al stock físico | Rechazado |
| Ajustar el stock a un valor menor al reservado | Rechazado |
| Crear un producto con una categoría que no existe | Rechazado |
| Intentar cambiar el `id` de un producto al editarlo | El id no cambia |
| Crear dos productos con el mismo `id` | El segundo se rechaza |
| Agregar al carrito un producto agotado | Rechazado |
| Entrar directo a la dirección de un producto inactivo para comprarlo | Rechazado |
| Editar el precio de un producto y revisar una orden anterior | La orden conserva el precio antiguo |

Estas pruebas sirven para el reporte de pruebas que pide el proyecto y para demostrar en la defensa que la base de datos está protegida.
