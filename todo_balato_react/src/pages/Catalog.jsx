
import { useCallback, useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import {
  listarProductosCatalogo,
  obtenerCategoriasCatalogo,
} from "../services/django";
import { clp } from "../utils/formato";

const PRECIO_MAX = 40000;

export default function Catalog({
  categoriaInicial = "",
  busqueda = "",
  onAgregar,
  onVerProducto,
}) {
  const [categorias, setCategorias] = useState([]);
  const [productos, setProductos] = useState([]);
  const [seleccionadas, setSeleccionadas] = useState(
    categoriaInicial ? [categoriaInicial] : []
  );
  const [precioMax, setPrecioMax] = useState(PRECIO_MAX);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  const cargarCatalogo = useCallback(async () => {
    setCargando(true);
    setError("");

    try {
      const [catsData, prodsData] = await Promise.all([
        obtenerCategoriasCatalogo(),
        listarProductosCatalogo({ page: 1, pageSize: 50 }),
      ]);

      setCategorias(
        Array.isArray(catsData?.results) ? catsData.results : []
      );

      setProductos(
        Array.isArray(prodsData?.results) ? prodsData.results : []
      );
    } catch (err) {
      setError(err?.message || "Error al cargar el catálogo.");
      setProductos([]);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarCatalogo();
  }, [cargarCatalogo]);

  const alternar = (catId) =>
    setSeleccionadas((s) =>
      s.includes(catId)
        ? s.filter((x) => x !== catId)
        : [...s, catId]
    );

  const texto = (busqueda || "").trim().toLowerCase();

  const visibles = productos.filter((p) => {
    const prodCats = Array.isArray(p.categorias)
      ? p.categorias.map((c) => c.id || c)
      : [];

    const coincideCategoria =
      seleccionadas.length === 0 ||
      seleccionadas.some((id) => prodCats.includes(id));

    const coincidePrecio =
      Number(p.precio ?? 0) <= precioMax;

    const coincideTexto =
      (p.nombre || "").toLowerCase().includes(texto);

    return coincideCategoria && coincidePrecio && coincideTexto;
  });

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
              />{" "}
              {c.nombre}
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
          onChange={(e) =>
            setPrecioMax(Number(e.target.value))
          }
        />
      </aside>

      <section>
        <h1 className="titulo-seccion">
          Catálogo de Productos
        </h1>

        {cargando && (
          <p role="status">Cargando catálogo...</p>
        )}

        {!cargando && error && (
          <div role="alert">
            <p>{error}</p>

            <button
              type="button"
              onClick={cargarCatalogo}
            >
              Reintentar
            </button>
          </div>
        )}

        {!cargando && !error && visibles.length === 0 && (
          <p>
            No hay productos que coincidan con tu búsqueda.
          </p>
        )}

        {!cargando && !error && visibles.length > 0 && (
          <div className="productos-grid">
            {visibles.map((p) => (
              <ProductCard
                key={p.id}
                {...p}
                onAgregarCarrito={onAgregar}
                onVerDetalle={onVerProducto}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
