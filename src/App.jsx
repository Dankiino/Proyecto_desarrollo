import { useState } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import AuthPage from "./pages/AuthPage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";

export default function App() {
  const [pagina, setPagina] = useState("inicio");

  const ir = (destino) => {
    setPagina(destino);
    window.scrollTo(0, 0);
  };

  const agregarCarrito = (id) => {
    alert(`Producto ${id} seleccionado (demostración)`);
  };

  return (
    <>
      <Navbar onNavegar={ir} />

      <main style={{ padding: "45px 20px", minHeight: "80vh", textAlign: "center" }}>
        {pagina === "inicio" && <Home onAgregarCarrito={agregarCarrito} />}
        {pagina === "catalogo" && <Catalog onAgregarCarrito={agregarCarrito} />}
        {pagina === "cuenta" && <AuthPage />}
        {pagina === "carrito" && <CartPage onContinuar={() => ir("pago")} />}
        {pagina === "pago" && <CheckoutPage />}
      </main>

      <Footer onNavegar={ir} />
    </>
  );
}
