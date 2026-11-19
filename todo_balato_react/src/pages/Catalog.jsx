import { useState } from "react";
import ProductCard from "../components/ProductCard";
import { productos, categorias } from "../data/productos";
import { clp } from "../utils/formato";

const PRECIO_MAX = 40000;

export default function Catalog({ categoriaInicial, busqueda, onAgregar }) {
  const [seleccionadas, setSeleccionadas] = useState(categoriaInicial ? [categoriaInicial] : []);
  const [precioMax, setPrecioMax] = useState(PRECIO_MAX);

  const alternar = (c) =>
    setSeleccionadas((s) => (s.includes(c) ? s.filter((x) => x !== c) : [...s, c]));

  const texto = busqueda.trim().toLowerCase();
  const visibles = productos.filter(
    (p) =>
      (seleccionadas.length === 0 || seleccionadas.includes(p.categoria)) &&
      p.precio <= precioMax &&
      p.nombre.toLowerCase().includes(texto)
  );

  return (
    <div className="catalogo">
      <aside className="filtros" aria-label="Filtros">
        <h2>Filtros</h2>
        <fieldset>
          <legend>Categoría</legend>
          {categorias.map((c) => (
            <label key={c}>
              <input type="checkbox" checked={seleccionadas.includes(c)} onChange={() => alternar(c)} /> {c}
            </label>
          ))}
        </fieldset>
        <label htmlFor="precio-max">Precio máximo: {clp(precioMax)}</label>
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
        <h1 className="titulo-seccion">Catálogo de Productos</h1>
        {visibles.length === 0 ? (
          <p>No hay productos que coincidan con tu búsqueda.</p>
        ) : (
          <div className="productos-grid">
            {visibles.map((p) => (
              <ProductCard key={p.id} {...p} onAgregarCarrito={onAgregar} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
