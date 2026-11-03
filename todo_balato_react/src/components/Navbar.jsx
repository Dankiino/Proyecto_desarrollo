const enlaces = [
  ["inicio", "Inicio"],
  ["catalogo", "Catálogo"],
  ["carrito", "Carrito"],
  ["cuenta", "Mi cuenta"],
];

export default function Navbar({ pagina, onNavegar, cantidadCarrito, busqueda, onBuscar }) {
  return (
    <header className="navbar">
      <button type="button" className="navbar-marca" onClick={() => onNavegar("inicio")}>
        <img src="/logo-todo-balato.png" alt="" />
        <span>TODO BALATO</span>
      </button>

      <nav aria-label="Principal">
        {enlaces.map(([id, texto]) => (
          <button
            key={id}
            type="button"
            className={`nav-link${pagina === id ? " activo" : ""}`}
            aria-current={pagina === id ? "page" : undefined}
            onClick={() => onNavegar(id)}
          >
            {texto}
            {id === "carrito" && cantidadCarrito > 0 ? ` (${cantidadCarrito})` : ""}
          </button>
        ))}
      </nav>

      <input
        type="search"
        placeholder="Buscar productos..."
        aria-label="Buscar productos"
        value={busqueda}
        onChange={(e) => onBuscar(e.target.value)}
      />
    </header>
  );
}
