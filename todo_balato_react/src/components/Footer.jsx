function Enlace({ a, onNavegar, children }) {
  return (
    <a
      href="#"
      onClick={(e) => {
        e.preventDefault();
        onNavegar(a);
      }}
    >
      {children}
    </a>
  );
}

export default function Footer({ onNavegar }) {
  return (
    <footer className="footer">
      <div className="footer-contenido">
        <div className="footer-marca">
          <img src="/logo-todo-balato.png" alt="Logo Todo Balato" className="footer-logo" />
          <h3>TODO BALATO</h3>
          <p>Bueno, bonito y barato.</p>
        </div>

        <div className="footer-enlaces">
          <h3>Navegación</h3>
          <Enlace a="inicio" onNavegar={onNavegar}>Inicio</Enlace>
          <Enlace a="catalogo" onNavegar={onNavegar}>Catálogo</Enlace>
          <Enlace a="cuenta" onNavegar={onNavegar}>Mi cuenta</Enlace>
        </div>

        <div className="footer-enlaces">
          <h3>Ayuda</h3>
          <Enlace a="carrito" onNavegar={onNavegar}>Mi carrito</Enlace>
          <Enlace a="pago" onNavegar={onNavegar}>Pagar</Enlace>
        </div>
      </div>

      <div className="footer-inferior">
        © {new Date().getFullYear()} Todo Balato. Todos los derechos reservados.
      </div>
    </footer>
  );
}
