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
          <a href="#" onClick={(e) => { e.preventDefault(); onNavegar("inicio"); }}>Inicio</a>
          <a href="#" onClick={(e) => { e.preventDefault(); onNavegar("catalogo"); }}>Catálogo</a>
        </div>

        <div className="footer-enlaces">
          <h3>Ayuda</h3>
          <a href="#" onClick={(e) => { e.preventDefault(); onNavegar("carrito"); }}>Mi carrito</a>
        </div>
      </div>

      <div className="footer-inferior">
        © {new Date().getFullYear()} Todo Balato. Todos los derechos reservados.
      </div>
    </footer>
  );
}
