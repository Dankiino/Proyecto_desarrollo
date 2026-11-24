import { useEffect, useRef, useState } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import AuthPage from "./pages/AuthPage";
import QuienesSomos from "./pages/QuienesSomos";
import ProductDetail from "./pages/ProductDetail";
import {
  calcularCarrito,
  combinarCarrito,
  crearOrden,
  guardarCantidad,
  login,
  logout,
  miUsuario,
  quitarDelCarrito,
  registro,
} from "./services/django";
import Contacto from "./pages/Contacto";

const CLAVE_CARRITO_ANONIMO = "todo_balato_carrito_anonimo";

function leerCarritoAnonimo() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE_CARRITO_ANONIMO));
    if (!Array.isArray(guardado)) return [];
    return guardado
      .filter(
        (item) => typeof item?.id === "string" && Number.isInteger(item.cantidad) && item.cantidad > 0,
      )
      .map(({ id, cantidad }) => ({ id, cantidad }));
  } catch {
    return [];
  }
}

const aCarritoReact = (items) =>
  items.map((item) => ({ id: item.producto_id, cantidad: item.cantidad }));

export default function App() {
  const [pagina, setPagina] = useState("inicio");
  const [productoId, setProductoId] = useState("");
  const [categoria, setCategoria] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [carrito, setCarrito] = useState(leerCarritoAnonimo); // [{ id, cantidad }]
  const [sesion, setSesion] = useState(null);
  const [cotizacion, setCotizacion] = useState(null);
  const [errorCarrito, setErrorCarrito] = useState("");
  const [orden, setOrden] = useState(null);
  const llaveOrden = useRef(null);





  useEffect(() => {
    // Con sesión iniciada el carrito vive en Comercio, no en el navegador.
    if (sesion) return;
    try {
      const anonimo = carrito.map(({ id, cantidad }) => ({ id, cantidad }));
      localStorage.setItem(CLAVE_CARRITO_ANONIMO, JSON.stringify(anonimo));
    } catch {
      // Sin almacenamiento disponible: el carrito sigue funcionando en memoria.
    }
  }, [carrito, sesion]);

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

  const guardarEnComercio = async (id, cantidad) => {
    try {
      const guardado = cantidad > 0
        ? await guardarCantidad(id, cantidad, sesion.access)
        : await quitarDelCarrito(id, sesion.access);
      setCarrito(aCarritoReact(guardado.items));
    } catch (error) {
      setErrorCarrito(error.message);
    }
  };

  const cantidadActual = (id) => carrito.find((i) => i.id === id)?.cantidad ?? 0;

  const agregar = (id, producto) => {
    setCotizacion(null);
    setErrorCarrito("");
    setOrden(null);
    llaveOrden.current = null;
    if (sesion) {
      guardarEnComercio(id, cantidadActual(id) + 1);
      return;
    }
    setCarrito((c) =>
      c.some((i) => i.id === id)
        ? c.map((i) => (
          i.id === id
            ? { ...i, cantidad: i.cantidad + 1, producto: producto || i.producto }
            : i
        ))
        : [...c, { id, cantidad: 1, producto }]
    );
  };

  const cambiarCantidad = (id, delta) => {
    setCotizacion(null);
    setErrorCarrito("");
    if (sesion) {
      guardarEnComercio(id, Math.max(cantidadActual(id) + delta, 0));
      return;
    }
    setCarrito((c) =>
      c.map((i) => (i.id === id ? { ...i, cantidad: i.cantidad + delta } : i)).filter((i) => i.cantidad > 0)
    );
  };

  const quitar = (id) => {
    setCotizacion(null);
    setErrorCarrito("");
    if (sesion) {
      guardarEnComercio(id, 0);
      return;
    }
    setCarrito((c) => c.filter((i) => i.id !== id));
  };

  const lineas = carrito.map((item) => {
    const producto = item.producto || {};
    const calculada = cotizacion?.lineas?.find((linea) => linea.producto_id === item.id);
    return {
      ...producto,
      id: item.id,
      cantidad: item.cantidad,
      nombre: calculada ? calculada.nombre : (producto.nombre || "Producto"),
      precio: calculada ? calculada.precio_unitario : producto.precio,
      subtotal: calculada?.subtotal,
      problema: calculada?.problema,
    };
  });
  const total = cotizacion?.total ?? lineas.reduce((suma, linea) => suma + (linea.precio ?? 0) * linea.cantidad, 0);
  const cantidadCarrito = carrito.reduce((suma, i) => suma + i.cantidad, 0);

  const verProducto = (id) => {
    setProductoId(id);
    setPagina("producto");
    window.scrollTo(0, 0);
  };

  const iniciarSesion = async (datos) => {
    const tokens = await login(datos);
    const usuario = await miUsuario(tokens.access);
    const anonimo = carrito.map((item) => ({ producto_id: item.id, cantidad: item.cantidad }));
    const guardado = await combinarCarrito(anonimo, tokens.access);
    try {
      localStorage.removeItem(CLAVE_CARRITO_ANONIMO);
    } catch {
      // Sin almacenamiento disponible: no hay nada que borrar.
    }
    setCotizacion(null);
    setErrorCarrito("");
    setCarrito(aCarritoReact(guardado.items));
    setSesion({ ...tokens, usuario });
    setPagina("carrito");
  };

  const crearCuenta = async (datos) => {
    await registro(datos);
  };

  const cerrarSesion = async () => {
    await logout(sesion.access, sesion.refresh);
    setSesion(null);
    setCarrito([]);
    setCotizacion(null);
    setErrorCarrito("");
  };

  const confirmarOrden = async () => {
    const items = carrito.map((item) => ({ producto_id: item.id, cantidad: item.cantidad }));
    llaveOrden.current ||= crypto.randomUUID();
    const respuesta = await crearOrden(items, cotizacion.total, sesion.access, llaveOrden.current);
    setOrden(respuesta.orden);
    llaveOrden.current = null;
    // El pedido ya se creó: se vacía también el carrito guardado en Comercio.
    await Promise.allSettled(carrito.map((item) => quitarDelCarrito(item.id, sesion.access)));
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

        {pagina === "inicio" && (
          <Home
            onNavegar={navegar}
            onAgregar={agregar}
            onVerProducto={verProducto}
          />
        )}

        {pagina === "quienes-somos" && (
          <QuienesSomos onNavegar={navegar} />
        )}

        {pagina === "catalogo" && (
          <Catalog
            key={categoria}
            categoriaInicial={categoria}
            busqueda={busqueda}
            onAgregar={agregar}
            onVerProducto={verProducto}
          />
        )}

        {pagina === "producto" && (
          <ProductDetail
            productoId={productoId}
            onVolver={() => navegar("catalogo")}
            onAgregar={agregar}
          />
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
        {pagina === "contacto" && <Contacto />}
      </main>

      <Footer onNavegar={navegar} />
    </>
  );
}