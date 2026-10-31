import Card from "../components/Card";
import Button from "../components/Button";

const productosPrueba = [

];

const CartPage = ({ onContinuar }) => {
  const totalGeneral = productosPrueba.reduce(
    (acc, prod) => acc + prod.precio * prod.cantidad,
    0
  );

  return (
    <Card titulo="Carrito de Compras">
      <div className="table-responsive">
        <table className="cart-table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Precio Unitario</th>
              <th>Cantidad</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {productosPrueba.map((prod) => (
              <tr key={prod.id}>
                <td>{prod.nombre}</td>
                <td>${prod.precio.toLocaleString("es-CL")}</td>
                <td>{prod.cantidad}</td>
                <td className="font-bold">
                  ${(prod.precio * prod.cantidad).toLocaleString("es-CL")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cart-footer">
        <h3>Total: ${totalGeneral.toLocaleString("es-CL")}</h3>
        <Button label="Continuar al Pago ➔" onClick={onContinuar} variant="primary" />
      </div>
    </Card>
  );
};

export default CartPage;