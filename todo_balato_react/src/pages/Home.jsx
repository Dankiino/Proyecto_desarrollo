import { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import { listarProductosCatalogo, obtenerCategoriasCatalogo } from "../services/django";

export default function Home({ onNavegar, onAgregar, onVerProducto }) {
  const [categorias, setCategorias] = useState([]);
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;
    Promise.all([
      obtenerCategoriasCatalogo(),
      listarProductosCatalogo({ page: 1, pageSize: 4 }),
    ])
      .then(([catsData, prodsData]) => {
        if (!vigente) return;
        setCategorias(Array.isArray(catsData?.results) ? catsData.results : []);
        setProductos(Array.isArray(prodsData?.results) ? prodsData.results : []);
      })
      .catch((solicitudError) => {
        if (vigente) setError(solicitudError?.message || "Error al cargar el inicio.");
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [intento]);

  const reintentar = () => {
    setError("");
    setCargando(true);
    setIntento((actual) => actual + 1);
  };

  return (
    <>
      <h1 className="titulo-marca">Bienvenido a Todo Balato</h1>
      <p>Bueno, bonito y barato.</p>

      <h2 className="subtitulo">Categorías</h2>
      <div className="categorias">
        {categorias.map((categoria) => (
          <button
            key={categoria.id}
            type="button"
            className="categoria-btn"
            onClick={() => onNavegar("catalogo", categoria.id)}
          >
            {categoria.nombre}
          </button>
        ))}
      </div>

      <h2 className="subtitulo">Productos destacados</h2>
      {cargando && <p role="status">Cargando productos destacados...</p>}
      {!cargando && error && (
        <div role="alert">
          <p>{error}</p>
          <button type="button" onClick={reintentar}>Reintentar</button>
        </div>
      )}
      {!cargando && !error && productos.length === 0 && (
        <p>No hay productos destacados disponibles.</p>
      )}
      {!cargando && !error && productos.length > 0 && (
        <div className="productos-grid">
          {productos.map((producto) => (
            <ProductCard
              key={producto.id}
              {...producto}
              onAgregarCarrito={onAgregar}
              onVerDetalle={onVerProducto}
            />
          ))}
        </div>
      )}
    </>
  );
}
