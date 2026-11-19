# Diseño de la base de datos de productos

Tienda online **Todo Balato** (un mall chino: hay de todo y es barato). Los precios van en pesos chilenos (CLP) y los productos y su stock se guardan en MongoDB, tal como pide el proyecto.

Cada producto tiene una "ficha" con todo lo importante, y todo el equipo debe conocer cómo es esa ficha antes de armar las pantallas. Los productos de ejemplo están en `mockData.json` y las reglas que deben cumplir los datos están en `validaciones.md`.

---

## 1. Colecciones

Una colección es una carpeta que guarda fichas del mismo tipo (equivale a una tabla). El servicio de Catálogo e Inventario tiene cuatro:

| Colección | Qué guarda |
|---|---|
| `productos` | Cada producto, con sus fotos y su stock |
| `categorias` | Los grupos de productos (Hogar, Cocina, Electrónica, etc.) |
| `reservas` | Las unidades apartadas por cada compra en proceso |
| `movimientos_stock` | El historial de cambios de stock: quién, cuándo y de qué valor a cuál |

Las reservas y los movimientos van aparte porque crecen sin límite (cada compra y cada ajuste agrega uno). Dentro del producto harían la ficha cada vez más pesada hasta superar el límite de 16 MB por documento de MongoDB.

---

## 2. La ficha del Producto

```json
{
  "_id": "prod_0001",
  "nombre": "Set de 6 vasos de vidrio",
  "descripcion": "Vasos de vidrio transparente de 300 ml, aptos para bebidas frías y calientes.",
  "precio": 3990,
  "moneda": "CLP",
  "stock_fisico": 120,
  "stock_reservado": 4,
  "categoria_id": "cocina",
  "imagenes": [
    { "url": "https://picsum.photos/seed/p01-1/800/800", "alt": "Set de vasos de vidrio, vista frontal" },
    { "url": "https://picsum.photos/seed/p01-2/800/800", "alt": "Vasos de vidrio apilados" },
    { "url": "https://picsum.photos/seed/p01-3/800/800", "alt": "Vaso de vidrio con bebida" },
    { "url": "https://picsum.photos/seed/p01-4/800/800", "alt": "Empaque del set de vasos" }
  ],
  "activo": true,
  "version": 1,
  "creado_en": "2026-10-12T14:00:00Z",
  "actualizado_en": "2026-10-12T14:00:00Z"
}
```

| Dato | Qué es |
|---|---|
| `_id` | Código único e inmutable del producto (ej. `prod_0001`). MongoDB lo llama `_id`; al llegar a React se muestra como `id` |
| `nombre` | Cómo se llama el producto |
| `descripcion` | Texto que explica el producto |
| `precio` | Precio en pesos enteros (3990 = $3.990). Se usan enteros porque el peso chileno no tiene decimales y así se evitan errores de redondeo |
| `moneda` | Siempre `"CLP"` |
| `stock_fisico` | Unidades que hay realmente en la bodega |
| `stock_reservado` | Unidades apartadas por clientes que están pagando. El administrador no lo edita a mano |
| `categoria_id` | Nombre corto de la categoría a la que pertenece (ej. `"cocina"`) |
| `imagenes` | Lista de 4 a 6 fotos. Cada una tiene su enlace (`url`) y un texto que la describe (`alt`) para personas que no pueden verla |
| `activo` | `true` si el producto está visible y a la venta, `false` si está apagado. Apagarlo no lo borra |
| `version` | Número que sube cada vez que se edita el producto. Evita que dos personas editen a la vez y se pisen los cambios |
| `creado_en` / `actualizado_en` | Fechas de creación y de última modificación |

### Stock físico, reservado y disponible

> **disponible = físico − reservado**

Ejemplo: el set de vasos tiene 120 físicos y 4 reservados, así que se pueden vender 116.

Durante una compra los números cambian así:
1. **Reservar** (el cliente va a pagar): sube el reservado. El físico no cambia.
2. **Confirmar** (el pago se aprueba): bajan el físico y el reservado.
3. **Liberar** (el pago se rechaza o se acaba el tiempo): baja solo el reservado.

El stock disponible **no se guarda** en la base: se calcula al enviar los datos a React.

---

## 3. La ficha de la Categoría

```json
{
  "_id": "cocina",
  "nombre": "Cocina",
  "descripcion": "Utensilios, vasos y organizadores para la cocina.",
  "orden": 2,
  "activa": true
}
```

| Dato | Qué es |
|---|---|
| `_id` | Nombre corto y único (*slug*): solo minúsculas, números y guiones. También sirve para armar direcciones como `/catalogo/cocina` |
| `nombre` | El nombre que ve el cliente ("Cocina") |
| `descripcion` | Texto corto que explica la categoría |
| `orden` | Número que define en qué orden se muestran |
| `activa` | Si la categoría se muestra o no |

---

## 4. Cómo se conectan productos y categorías

Cada producto guarda en `categoria_id` el nombre corto de su categoría. No copia sus datos, solo apunta a ella:

```
Producto "Set de 6 vasos"  →  categoria_id: "cocina"  →  Categoría "Cocina"
```

Así, si una categoría se renombra, se cambia en una sola ficha y todos sus productos quedan actualizados. Para mostrar una categoría, React pide los productos con una dirección como `/productos?categoria=cocina`.

Las fotos, en cambio, van dentro de la ficha del producto: son pocas y siempre se muestran junto a él.

---

## 5. Tips para cuidar el espacio del plan gratuito

- Confirmar la cuota vigente del plan gratuito de Atlas (M0) antes del primer hito; hoy ofrece 512 MB. Un producto ocupa entre 1 y 2 KB, así que caben miles.
- Guardar solo los **enlaces** de las fotos, nunca las fotos.
- Usar enlaces **permanentes**: el proyecto pide que un producto se pueda consultar sin depender de archivos temporales.
- No guardar datos que se pueden calcular, como el stock disponible.
- No repetir datos: por eso la categoría va por referencia.
- Crear solo los índices necesarios. Un índice acelera las búsquedas pero ocupa espacio; por ahora basta uno: `{ activo: 1, categoria_id: 1 }`, para el catálogo público filtrado por categoría.
- Mostrar los productos por páginas: el proyecto limita a 50 como máximo por respuesta.
