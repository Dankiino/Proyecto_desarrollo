import { useState } from "react";
import Card from "../components/Card";
import Button from "../components/Button";
import { clp } from "../utils/formato";

export default function CheckoutPage({ lineas, total, sesion, orden, puedePagar, onConfirmar, onNavegar }) {
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const confirmar = async (evento) => {
    evento.preventDefault();
    setError("");
    setCargando(true);
    try {
      await onConfirmar();
    } catch (solicitudError) {
      setError(solicitudError.message);
    } finally {
      setCargando(false);
    }
  };

  if (orden) {
    return (
      <Card titulo="Pedido creado">
        <p>Pedido {orden.id}, estado {orden.estado}. No se realizó ningún cobro.</p>
        <p className="text-center"><Button label="Seguir comprando" onClick={() => onNavegar("catalogo")} /></p>
      </Card>
    );
  }

  if (lineas.length === 0) {
    return (
      <Card titulo="Checkout">
        <p>No tienes productos en el carrito.</p>
        <p className="text-center"><Button label="Ver catálogo" onClick={() => onNavegar("catalogo")} /></p>
      </Card>
    );
  }

  return (
    <div className="checkout-grid">
      <Card titulo="1. Resumen del Pedido">
        <ul className="checkout-list">
          {lineas.map((l) => (
            <li key={l.id}>
              <span>{l.cantidad}x {l.nombre}</span>
              <strong>{clp(l.subtotal ?? l.precio * l.cantidad)}</strong>
            </li>
          ))}
        </ul>
        <hr className="divider" />
        <div className="checkout-total">
          <span>Total del pedido:</span>
          <span className="total-monto">{clp(total)}</span>
        </div>
      </Card>

      <Card titulo="2. Confirmar Pedido">
        {!sesion ? (
          <>
            <p>Debes iniciar sesión para confirmar el pedido.</p>
            <Button label="Iniciar sesión" onClick={() => onNavegar("cuenta")} />
          </>
        ) : (
          <form onSubmit={confirmar} className="auth-form">
            <p>El pedido quedará pendiente de pago. Esta versión no procesa pagos.</p>
            {error && <p role="alert">{error}</p>}
            <Button label={cargando ? "Creando pedido..." : `Crear pedido por ${clp(total)}`}
              disabled={!puedePagar || cargando}
              type="submit" />
          </form>
        )}
      </Card>
    </div>
  );
}
