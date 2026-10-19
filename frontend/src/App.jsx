
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import ProductCard from "./components/ProductCard";

const productosPrueba = [
  {
    id: "1",
    nombre: "Audífonos Bluetooth",
    precio: 12990,
    moneda: "CLP",
    imagen_principal: null,
    disponible: true,
  },
  {
    id: "2",
    nombre: "Mochila urbana",
    precio: 24990,
    moneda: "CLP",
    imagen_principal: null,
    disponible: true,
  },
  {
    id: "3",
    nombre: "Lámpara LED",
    precio: 8990,
    moneda: "CLP",
    imagen_principal: null,
    disponible: true,
  },
  {
    id: "4",
    nombre: "Teclado mecánico",
    precio: 35990,
    moneda: "CLP",
    imagen_principal: null,
    disponible: false,
  },
];

export default function App() {
  const agregarCarrito = (id) => {
    alert(`Producto ${id} seleccionado (demostración)`);
  };

  return (
    <>
      <Navbar />

      <main
        style={{
          padding: "45px 20px",
          backgroundColor: "#F9EBAC",
          minHeight: "80vh",
          color: "#171717",
          textAlign: "center",
        }}
      >
        <h1 style={{ color: "#BE1A19" }}>
          Bienvenido a Todo Balato
        </h1>

        <p>Bueno, bonito y barato.</p>

        <h2 style={{ marginTop: "45px" }}>
          Productos destacados
        </h2>

        <div className="productos-grid">
          {productosPrueba.map((producto) => (
            <ProductCard
              key={producto.id}
              {...producto}
              onAgregarCarrito={agregarCarrito}
            />
          ))}
        </div>
      </main>

      <Footer />
    </>
  );
}
