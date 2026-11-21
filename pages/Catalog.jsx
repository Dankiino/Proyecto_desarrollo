
import { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import { obtenerProductos, obtenerCategorias } from "../services/django";
import { clp } from "../utils/formato";

const PRECIO_MAX = 40000;
const LIMITE = 20;

export default function Catalog({ categoriaInicial, busqueda, onAgregar }) {
  const [seleccionadas, setSeleccionadas] = useState(
    categoriaInicial ? [categoriaInicial] : []
  );

  const [precioMax, setPrecioMax] = useState(PRECIO_MAX);
  const [productos, setProductos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  // Obtener categorías desde Django
  useEffect(() => {
    async function cargarCategorias() {
      try {
        const respuesta = await obtenerCategorias();
        setCategorias(respuesta.resultados || []);
      } catch (err) {
        setError(err.message);
      }
    }

    cargarCategorias();
  }, []);

  // Obtener productos desde Django
  useEffect(() => {
    let activo = true;

    async function cargarProductos() {
      setCargando(true);
      setError("");

      try {
        const respuesta = await obtenerProductos(pagina, LIMITE);

        if (!activo) return;

        setProductos(respuesta.resultados || []);
        setTotalPaginas(respuesta.paginacion?.total_paginas || 1);
      } catch (err) {
        if (activo) setError(err.message);
      } finally {
        if (activo) setCargando(false);
      }
    }

    cargarProductos();

    return () => {
      activo = false;
    };
  }, [pagina]);

  const alternar = (id) => {
    setSeleccionadas((actuales) =>
      actuales.includes(id)
        ? actuales.filter((x) => x !== id)
        : [...actuales, id]
    );

    setPagina(1);
  };

  const texto = (busqueda || "").trim().toLowerCase();

  const visibles = productos.filter(
    (p) =>
      (seleccionadas.length === 0 ||
        seleccionadas.includes(p.categoria_id)) &&
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
            <label key={c.id}>
              <input
                type="checkbox"
                checked={seleccionadas.includes(c.id)}
                onChange={() => alternar(c.id)}
              />
              {" "}{c.nombre}
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
        <h1 className="titulo-seccion">Catálogo de Productos</h1>

        {cargando ? (
          <p>Cargando productos...</p>
        ) : error ? (
          <p role="alert">{error}</p>
        ) : visibles.length === 0 ? (
          <p>No hay productos que coincidan con tu búsqueda.</p>
        ) : (
          <div className="productos-grid">
            {visibles.map((p) => (
              <ProductCard
                key={p.id}
                {...p}
                onAgregarCarrito={onAgregar}
              />
            ))}
          </div>
        )}

        {!cargando && !error && totalPaginas > 1 && (
          <div className="paginacion">
            <button
              type="button"
              disabled={pagina === 1}
              onClick={() => setPagina((actual) => actual - 1)}
            >
              Anterior
            </button>

            <span>
              Página {pagina} de {totalPaginas}
            </span>

            <button
              type="button"
              disabled={pagina >= totalPaginas}
              onClick={() => setPagina((actual) => actual + 1)}
            >
              Siguiente
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
