import Card from "../components/Card";
import Button from "../components/Button";
import { clp } from "../utils/formato";

const MENSAJES_PROBLEMA = {
  no_existe: "Este producto ya no existe en el catálogo. Quítalo para continuar.",
  inactivo: "Este producto ya no está a la venta. Quítalo para continuar.",
  agotado: "Este producto está agotado. Quítalo para continuar.",
  stock_insuficiente: "No hay stock suficiente para esta cantidad. Reduce las unidades para continuar.",
};

export default function CartPage({
  lineas,
  total,
  cargando,
  error,
  puedePagar,
  onCambiar,
  onQuitar,
  onNavegar,
}) {
  if (lineas.length === 0) {
    return (
      <Card titulo="Carrito de Compras">
        <p>Tu carrito está vacío.</p>
        <p className="text-center">
          <Button label="Ver catálogo" onClick={() => onNavegar("catalogo")} />
        </p>
      </Card>
    );
  }

  const hayProblemas = lineas.some((l) => l.problema);

  return (
    <Card titulo="Carrito de Compras">
      {cargando && <p>Consultando precios y existencias...</p>}
      {error && <p role="alert">{error}</p>}
      {hayProblemas && (
        <p role="alert">
          Algunos productos de tu carrito ya no están disponibles o no tienen stock suficiente.
          Revisa los avisos en cada fila.
        </p>
      )}
      <div className="table-responsive">
        <table className="cart-table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Precio</th>
              <th>Cantidad</th>
              <th>Subtotal</th>
              <th><span className="sr-only">Quitar</span></th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((l) => (
              <tr key={l.id}>
                <td>
                  {l.nombre || "Producto no disponible"}
                  {l.problema && (
                    <small style={{ display: "block", color: "#8b0000" }}>
                      {MENSAJES_PROBLEMA[l.problema] || "Este producto no está disponible."}
                    </small>
                  )}
                </td>
                <td>{l.precio != null ? clp(l.precio) : "—"}</td>
                <td>
                  <div className="cantidad">
                    <button type="button" className="btn btn-secondary btn-sm"
                      aria-label={`Quitar una unidad de ${l.nombre || "producto"}`} onClick={() => onCambiar(l.id, -1)}>−</button>
                    <span>{l.cantidad}</span>
                    <button type="button" className="btn btn-secondary btn-sm"
                      aria-label={`Agregar una unidad de ${l.nombre || "producto"}`} onClick={() => onCambiar(l.id, 1)}>+</button>
                  </div>
                </td>
                <td className="font-bold">{l.problema ? "No disponible" : clp(l.subtotal ?? l.precio * l.cantidad)}</td>
                <td><button type="button" className="btn-link" onClick={() => onQuitar(l.id)}>Quitar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cart-footer">
        <h3>Total: {clp(total)}</h3>
        <Button label="Continuar al Pago ➔" disabled={cargando || !puedePagar}
          onClick={() => onNavegar("pago")} />
      </div>
    </Card>
  );
}