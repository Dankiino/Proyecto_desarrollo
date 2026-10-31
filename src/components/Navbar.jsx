const link = { color: "white", background: "none", border: "none", fontSize: "1rem" };

export default function Navbar({ onNavegar }) {
  return (
    <header style={{
      backgroundColor: "#BE1A19", padding: "15px 30px", display: "flex", alignItems: "center",
      justifyContent: "space-between", gap: "20px", flexWrap: "wrap", color: "white",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <img src="/logo-todo-balato.png" alt="Todo Balato"
          style={{ width: "65px", height: "65px", objectFit: "contain" }} />
        <h2>TODO BALATO</h2>
      </div>

      <nav style={{ display: "flex", gap: "20px" }}>
        <button style={link} onClick={() => onNavegar("inicio")}>Inicio</button>
        <button style={link} onClick={() => onNavegar("catalogo")}>Catálogo</button>
        <button style={link} onClick={() => onNavegar("carrito")}>Carrito</button>
        <button style={link} onClick={() => onNavegar("cuenta")}>Mi cuenta</button>
      </nav>

      <input type="search" placeholder="Buscar productos..." aria-label="Buscar productos"
        style={{ padding: "12px", borderRadius: "6px", border: "none" }} />
    </header>
  );
}
