import ProductCard from "../components/ProductCard";
import { productos } from "../data/productos";

export default function Home({ onAgregarCarrito }) {
  return (
    <>
      <h1 style={{ color: "#BE1A19" }}>Bienvenido a Todo Balato</h1>
      <p>Bueno, bonito y barato.</p>

      <h2 style={{ marginTop: "45px" }}>Productos destacados</h2>
      <div className="productos-grid">
        {productos.map((p) => (
          <ProductCard key={p.id} {...p} onAgregarCarrito={onAgregarCarrito} />
        ))}
      </div>
    </>
  );
}
