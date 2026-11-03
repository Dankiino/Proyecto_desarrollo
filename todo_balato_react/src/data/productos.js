import catalogo from "./mockCatalogo.json";

const nombresCategoria = Object.fromEntries(
  catalogo.categorias.map((categoria) => [categoria.id, categoria.nombre]),
);

export const productos = catalogo.productos.map((producto) => ({
  id: producto.id,
  nombre: producto.nombre,
  precio: producto.precio,
  categoria: nombresCategoria[producto.categoria_id] || "Otros",
  moneda: producto.moneda,
  disponible: producto.activo && producto.stock_fisico > producto.stock_reservado,
  imagen_principal: producto.imagenes?.[0]
    ? { url: producto.imagenes[0].url, texto_alternativo: producto.imagenes[0].alt }
    : null,
}));

export const categorias = catalogo.categorias
  .filter((categoria) => categoria.activa)
  .sort((a, b) => a.orden - b.orden)
  .map((categoria) => categoria.nombre);
