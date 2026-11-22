
import { useState } from "react";
import ProductCard from "../components/ProductCard";
import { categorias } from "../data/productos";
import { clp } from "../utils/formato";

const PRECIO_MAX = 40000;

export default function Catalog({
  categoriaInicial = "",
  busqueda = "",
  onAgregar,
  productos = [],
  cargando = false,
  error = "",
}) {
  const [seleccionadas, setSeleccionadas] = useState(
    categoriaInicial ? [categoriaInicial] : []
  );

  const [precioMax, setPrecioMax] = useState(PRECIO_MAX);

  const alternar = (categoria) => {
    setSeleccionadas((actuales) =>
      actuales.includes(categoria)
        ? actuales.filter((c) => c !== categoria)
        : [...actuales, categoria]
    );
  };

  const texto = busqueda.trim().toLowerCase();

  const visibles = productos.filter((producto) => {
    const categoriaProducto = producto.categoria_id;

    const cumpleCategoria =
      seleccionadas.length === 0 ||
      seleccionadas.some(
        (categoria) =>
          categoriaProducto === categoria.toLowerCase() ||
          categoriaProducto === categoria
      );

    const cumplePrecio = producto.precio <= precioMax;

    const cumpleBusqueda =
      producto.nombre.toLowerCase().includes(texto);

    return cumpleCategoria && cumplePrecio && cumpleBusqueda;
  });

  return (
    <div className="catalogo">
      <aside className="filtros" aria-label="Filtros">
        <h2>Filtros</h2>

        <fieldset>
          <legend>Categorías</legend>

          {categorias.map((categoria) => (
            <label key={categoria}>
              <input
                type="checkbox"
                checked={seleccionadas.includes(categoria)}
                onChange={() => alternar(categoria)}
              />
              {" "}{categoria}
            </label>
          ))}
        </fieldset>

        <label htmlFor="precio-max">
          Precio máximo: {clp(precioMax)}
        </label>

        <input
          id="precio-max"
          type="range"
          min="0"
          max={PRECIO_MAX}
          step="1000"
          value={precioMax}
          onChange={(e) => setPrecioMax(Number(e.target.value))}
        />
      </aside>

      <section>
        <h1 className="titulo-seccion">
          Catálogo de Productos
        </h1>

        {cargando ? (
          <p>Cargando productos...</p>
        ) : error ? (
          <p role="alert">{error}</p>
        ) : visibles.length === 0 ? (
          <p>No hay productos que coincidan con tu búsqueda.</p>
        ) : (
          <div className="productos-grid">
            {visibles.map((producto) => (
              <ProductCard
                key={producto.id}
                {...producto}
                onAgregarCarrito={onAgregar}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
