import { useEffect, useRef, useState } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import AuthPage from "./pages/AuthPage";
import { productos } from "./data/productos";
import {
  calcularCarrito,
  crearOrden,
  login,
  logout,
  miUsuario,
  registro,
} from "./services/django";

export default function App() {
  const [pagina, setPagina] = useState("inicio");
  const [categoria, setCategoria] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [carrito, setCarrito] = useState([]); // [{ id, cantidad }]
  const [sesion, setSesion] = useState(null);
  const [cotizacion, setCotizacion] = useState(null);
  const [errorCarrito, setErrorCarrito] = useState("");
  const [orden, setOrden] = useState(null);
  const llaveOrden = useRef(null);

  useEffect(() => {
    if (carrito.length === 0) {
      return undefined;
    }

    let vigente = true;
    const items = carrito.map((item) => ({ producto_id: item.id, cantidad: item.cantidad }));

    calcularCarrito(items)
      .then((resultado) => {
        if (vigente) setCotizacion(resultado);
      })
      .catch((error) => {
        if (vigente) setErrorCarrito(error.message);
      });

    return () => {
      vigente = false;
    };
  }, [carrito]);

  const navegar = (destino, cat = "") => {
    setCategoria(cat);
    setBusqueda("");
    setPagina(destino);
    window.scrollTo(0, 0);
  };

  const buscar = (texto) => {
    setBusqueda(texto);
    setPagina("catalogo");
  };

  const agregar = (id) => {
    setCotizacion(null);
    setErrorCarrito("");
    setOrden(null);
    llaveOrden.current = null;
    setCarrito((c) =>
      c.some((i) => i.id === id)
        ? c.map((i) => (i.id === id ? { ...i, cantidad: i.cantidad + 1 } : i))
        : [...c, { id, cantidad: 1 }]
    );
  };

  const cambiarCantidad = (id, delta) => {
    setCotizacion(null);
    setErrorCarrito("");
    setCarrito((c) =>
      c.map((i) => (i.id === id ? { ...i, cantidad: i.cantidad + delta } : i)).filter((i) => i.cantidad > 0)
    );
  };

  const quitar = (id) => {
    setCotizacion(null);
    setErrorCarrito("");
    setCarrito((c) => c.filter((i) => i.id !== id));
  };

  const lineas = carrito.map((item) => {
    const producto = productos.find((p) => p.id === item.id);
    const calculada = cotizacion?.lineas?.find((linea) => linea.producto_id === item.id);
    return {
      ...producto,
      cantidad: item.cantidad,
      nombre: calculada?.nombre || producto?.nombre,
      precio: calculada?.precio_unitario ?? producto?.precio,
      subtotal: calculada?.subtotal,
      problema: calculada?.problema,
    };
  });
  const total = cotizacion?.total ?? lineas.reduce((suma, linea) => suma + linea.precio * linea.cantidad, 0);
  const cantidadCarrito = carrito.reduce((suma, i) => suma + i.cantidad, 0);

  const iniciarSesion = async (datos) => {
    const tokens = await login(datos);
    const usuario = await miUsuario(tokens.access);
    setSesion({ ...tokens, usuario });
    setPagina("carrito");
  };

  const crearCuenta = async (datos) => {
    await registro(datos);
  };

  const cerrarSesion = async () => {
    await logout(sesion.access, sesion.refresh);
    setSesion(null);
  };

  const confirmarOrden = async () => {
    const items = carrito.map((item) => ({ producto_id: item.id, cantidad: item.cantidad }));
    llaveOrden.current ||= crypto.randomUUID();
    const respuesta = await crearOrden(items, cotizacion.total, sesion.access, llaveOrden.current);
    setOrden(respuesta.orden);
    llaveOrden.current = null;
    setCarrito([]);
  };

  return (
    <>
      <Navbar
        pagina={pagina}
        onNavegar={navegar}
        cantidadCarrito={cantidadCarrito}
        busqueda={busqueda}
        onBuscar={buscar}
      />

      <main className="contenido">
        {pagina === "inicio" && <Home onNavegar={navegar} onAgregar={agregar} />}
        {pagina === "catalogo" && (
          <Catalog key={categoria} categoriaInicial={categoria} busqueda={busqueda} onAgregar={agregar} />
        )}
        {pagina === "carrito" && (
          <CartPage
            lineas={lineas}
            total={total}
            cargando={Boolean(carrito.length && !cotizacion && !errorCarrito)}
            error={errorCarrito}
            puedePagar={Boolean(cotizacion?.puede_pagar)}
            onCambiar={cambiarCantidad}
            onQuitar={quitar}
            onNavegar={navegar}
          />
        )}
        {pagina === "pago" && (
          <CheckoutPage
            lineas={lineas}
            total={total}
            sesion={sesion}
            orden={orden}
            puedePagar={Boolean(cotizacion?.puede_pagar)}
            onConfirmar={confirmarOrden}
            onNavegar={navegar}
          />
        )}
        {pagina === "cuenta" && (
          <AuthPage
            sesion={sesion}
            onLogin={iniciarSesion}
            onRegistro={crearCuenta}
            onLogout={cerrarSesion}
          />
        )}
      </main>

      <Footer onNavegar={navegar} />
    </>
  );
}
