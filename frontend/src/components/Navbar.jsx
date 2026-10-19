
export default function Navbar() {
    return (
        <header style={{
            backgroundColor: "#BE1A19",
            padding: "15px 30px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "20px",
            flexWrap: "wrap",
            color: "white"
        }}>
            <div style={{
                display: "flex",
                alignItems: "center",
                gap: "12px"
            }}>
                <img
                    src="/logo-todo-balato.png"
                    alt="Todo Balato"
                    style={{ width: "65px", height: "65px", objectFit: "contain" }}
                />
                <h2>TODO BALATO</h2>
            </div>

            <nav style={{ display: "flex", gap: "20px" }}>
                <a href="/" style={{ color: "white" }}>Inicio</a>
                <a href="/catalogo" style={{ color: "white" }}>Catálogo</a>
                <a href="/contacto" style={{ color: "white" }}>Contacto</a>
            </nav>

            <input
                type="search"
                placeholder="Buscar productos..."
                aria-label="Buscar productos"
                style={{
                    padding: "12px",
                    borderRadius: "6px",
                    border: "none"
                }}
            />
        </header>
    );
}
