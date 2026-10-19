
export default function ProductCard({
    id,
    nombre = "Producto sin nombre",
    precio = 0,
    moneda = "CLP",
    imagen_principal = null,
    disponible = true,
    onAgregarCarrito = () => { },
}) {
    const precioFormateado = new Intl.NumberFormat("es-CL", {
        style: "currency",
        currency: moneda,
        maximumFractionDigits: 0,
    }).format(precio);

    return (
        <article className="producto-card">
            <div className="producto-imagen">
                {imagen_principal?.url ? (
                    <img
                        src={imagen_principal.url}
                        alt={imagen_principal.texto_alternativo || nombre}
                        loading="lazy"
                    />
                ) : (
                    <div className="producto-placeholder">
                        <span>📦</span>
                        <p>Sin imagen</p>
                    </div>
                )}
            </div>

            <div className="producto-info">
                <h3>{nombre}</h3>

                <p className="producto-precio">
                    {precioFormateado}
                </p>

                <p className={
                    disponible ? "producto-disponible" : "producto-agotado"
                }>
                    {disponible ? "Disponible" : "Agotado"}
                </p>

                <button
                    type="button"
                    className="producto-boton"
                    disabled={!disponible}
                    onClick={() => onAgregarCarrito(id)}
                >
                    {disponible ? "Agregar al Carrito" : "Sin stock"}
                </button>
            </div>
        </article>
    );
}
