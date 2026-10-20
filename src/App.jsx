import { useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import AuthPage from "./pages/AuthPage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import Button from "./components/Button";
import "./App.css";

const App = () => {
  // Estado para simular la navegación transaccional entre vistas
  const [vistaActual, setVistaActual] = useState("auth");

  return (
    <div className="app-container">
      <Header 
        title="TODO BALATO 🛒" 
        description="¡Bueno, bonito y balato!" 
      />

      {/* Navegación para validar las pantallas */}
      <nav className="nav-bar">
        <Button 
          label="1. Registro / Login" 
          variant={vistaActual === "auth" ? "primary" : "secondary"} 
          onClick={() => setVistaActual("auth")} 
        />
        <Button 
          label="2. Carrito de Compras" 
          variant={vistaActual === "cart" ? "primary" : "secondary"} 
          onClick={() => setVistaActual("cart")} 
        />
        <Button 
          label="3. Checkout (Pago)" 
          variant={vistaActual === "checkout" ? "primary" : "secondary"} 
          onClick={() => setVistaActual("checkout")} 
        />
      </nav>

      {/* Contenido según la pantalla seleccionada */}
      <main className="main-content">
        {vistaActual === "auth" && <AuthPage />}
        {vistaActual === "cart" && <CartPage onContinuar={() => setVistaActual("checkout")} />}
        {vistaActual === "checkout" && <CheckoutPage />}
      </main>

      <Footer course="Desarrollo de Aplicaciones Web" />
    </div>
  );
};

export default App;