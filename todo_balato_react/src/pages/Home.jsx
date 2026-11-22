import ProductCard from "../components/ProductCard";
import { categorias } from "../data/productos";

export default function Home({
  onNavegar,
  onAgregar,
  productos = [],
  cargando = false,
  error = "",
}) {
  return (
    <>
      <h1 className="titulo-marca">Bienvenido a Todo Balato</h1>
      <p>Bueno, bonito y barato.</p>

      <h2 className="subtitulo">Categorías</h2>
      <div className="categorias">
        {categorias.map((c) => (
          <button key={c} type="button" className="categoria-btn" onClick={() => onNavegar("catalogo", c)}>
            {c}
          </button>
        ))}
      </div>

      <h2 className="subtitulo">Productos destacados</h2>

        {cargando ? (
          <p>Cargando productos...</p>
        ) : error ? (
          <p role="alert">{error}</p>
        ) : productos.length === 0 ? (
          <p>No hay productos disponibles.</p>
        ) : (
          <div className="productos-grid">
            {productos.slice(0, 4).map((p) => (
              <ProductCard
                key={p.id}
                {...p}
                onAgregarCarrito={onAgregar}
              />
            ))}
          </div>
        )}
    </>
  );
}
