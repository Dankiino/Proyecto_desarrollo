import Card from "../components/Card";
import Button from "../components/Button";
import { clp } from "../utils/formato";

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

  return (
    <Card titulo="Carrito de Compras">
      {cargando && <p>Consultando precios y existencias...</p>}
      {error && <p role="alert">{error}</p>}
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
                <td>{l.nombre}</td>
                <td>{clp(l.precio)}</td>
                <td>
                  <div className="cantidad">
                    <button type="button" className="btn btn-secondary btn-sm"
                      aria-label={`Quitar una unidad de ${l.nombre}`} onClick={() => onCambiar(l.id, -1)}>−</button>
                    <span>{l.cantidad}</span>
                    <button type="button" className="btn btn-secondary btn-sm"
                      aria-label={`Agregar una unidad de ${l.nombre}`} onClick={() => onCambiar(l.id, 1)}>+</button>
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
