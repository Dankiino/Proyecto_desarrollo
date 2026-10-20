import Card from "../components/Card";
import Button from "../components/Button";

const CheckoutPage = () => {
  return (
    <div className="checkout-grid">
      {/* Columna 1: Resumen Estático del Pedido */}
      <Card titulo="1. Resumen del Pedido">
        <ul className="checkout-list">
          <li>
            <span>2x Cuaderno Universitario</span>
            <strong>$5.000</strong>
          </li>
          <li>
            <span>1x Set de Destacadores</span>
            <strong>$4.990</strong>
          </li>
          <li>
            <span>1x Calculadora Científica</span>
            <strong>$15.990</strong>
          </li>
        </ul>
        <hr className="divider" />
        <div className="checkout-total">
          <span>Total a pagar:</span>
          <span className="total-monto">$25.980</span>
        </div>
      </Card>

      {/* Columna 2: Formulario Visual de Pago */}
      <Card titulo="2. Datos de Pago">
        <form onSubmit={(e) => e.preventDefault()} className="auth-form">
          <div className="form-group">
            <label>Titular de la Tarjeta</label>
            <input type="text" placeholder="Nombre como aparece en la tarjeta" className="task-input" />
          </div>

          <div className="form-group">
            <label>Número de Tarjeta</label>
            <input type="text" placeholder="1234 5678 9101 1121" className="task-input" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Expiración</label>
              <input type="text" placeholder="MM/AA" className="task-input" />
            </div>
            <div className="form-group">
              <label>CVC / CVV</label>
              <input type="password" placeholder="123" className="task-input" maxLength={4} />
            </div>
          </div>

          <Button label="Pagar $25.980" variant="success" type="submit" />
        </form>
      </Card>
    </div>
  );
};

export default CheckoutPage;