import ProductCard from "../components/ProductCard";
import { productos } from "../data/productos";

export default function Catalog({ onAgregarCarrito }) {
  return (
    <div style={{ display: "flex", gap: "20px", maxWidth: "1200px", margin: "0 auto", textAlign: "left" }}>
      {/* Barra lateral de filtros (solo visual por ahora) */}
      <aside style={{ width: "200px", borderRight: "1px solid #ddd", paddingRight: "15px" }}>
        <h3>Filtros</h3>
        <h4>Categoría</h4>
        <label><input type="checkbox" /> Tecnología</label><br />
        <label><input type="checkbox" /> Accesorios</label><br />
        <label><input type="checkbox" /> Hogar</label>
        <h4>Precio</h4>
        <input type="range" aria-label="Precio máximo" />
      </aside>

      <section style={{ flex: 1 }}>
        <h2>Catálogo de Productos</h2>
        <div className="productos-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))" }}>
          {productos.map((p) => (
            <ProductCard key={p.id} {...p} onAgregarCarrito={onAgregarCarrito} />
          ))}
        </div>
      </section>
    </div>
  );
}
