import { useEffect, useState } from "react";
import { obtenerProductoCatalogo } from "../services/django";
import { clp } from "../utils/formato";

export default function ProductDetail({ productoId, onVolver, onAgregar }) {
  const [producto, setProducto] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;
    obtenerProductoCatalogo(productoId)
      .then((resultado) => {
        if (vigente) setProducto(resultado);
      })
      .catch((solicitudError) => {
        if (vigente) setError(solicitudError?.message || "Error al cargar el producto.");
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [productoId, intento]);

  const reintentar = () => {
    setProducto(null);
    setError("");
    setCargando(true);
    setIntento((actual) => actual + 1);
  };

  if (cargando) {
    return <p role="status">Cargando producto...</p>;
  }

  if (error || !producto) {
    return (
      <section>
        <div role="alert">
          <p>{error || "El producto no existe o no está disponible."}</p>
          {error && <button type="button" onClick={reintentar}>Reintentar</button>}
        </div>
        <button type="button" className="btn btn-secondary" onClick={onVolver}>
          Volver al catálogo
        </button>
      </section>
    );
  }

  return (
    <section className="producto-detalle">
      <button type="button" className="btn btn-secondary" onClick={onVolver}>
        Volver al catálogo
      </button>
      <h1>{producto.nombre}</h1>
      <p className="producto-precio">{clp(producto.precio)}</p>
      <p className={producto.disponible ? "producto-disponible" : "producto-agotado"}>
        {producto.disponible ? "Disponible" : "Agotado"}
      </p>
      <p>{producto.descripcion}</p>
      <div className="producto-galeria">
        {(producto.imagenes || []).map((imagen, indice) => (
          <img
            key={`${imagen.url}-${indice}`}
            src={imagen.url}
            alt={imagen.texto_alternativo || producto.nombre}
            loading="lazy"
          />
        ))}
      </div>
      {producto.imagenes?.length === 0 && <p>Este producto no tiene imágenes disponibles.</p>}
      <button
        type="button"
        className="producto-boton"
        disabled={!producto.disponible}
        onClick={() => onAgregar(producto.id, {
          ...producto,
          imagen_principal: producto.imagen_principal || producto.imagenes?.[0] || null,
        })}
      >
        {producto.disponible ? "Agregar al Carrito" : "Sin stock"}
      </button>
    </section>
  );
}
