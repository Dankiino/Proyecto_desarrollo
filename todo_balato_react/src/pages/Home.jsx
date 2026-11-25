
import { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import {
  listarProductosCatalogo,
  obtenerCategoriasCatalogo,
} from "../services/django";
import { campo, textoAlternativo } from "../services/contenidos";

const RUTAS_INTERNAS = {
  "/": "inicio",
  "/inicio": "inicio",
  "/catalogo": "catalogo",
  "/contacto": "contacto",
  "/quienes-somos": "quienes-somos",
  "/carrito": "carrito",
};

export default function Home({
  contenidos,
  onNavegar,
  onAgregar,
  onVerProducto,
}) {
  const [categorias, setCategorias] = useState([]);
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;

    Promise.all([
      obtenerCategoriasCatalogo(),
      listarProductosCatalogo({ page: 1, pageSize: 4 }),
    ])
      .then(([catsData, prodsData]) => {
        if (!vigente) return;

        setCategorias(
          Array.isArray(catsData?.results)
            ? catsData.results
            : []
        );

        setProductos(
          Array.isArray(prodsData?.results)
            ? prodsData.results
            : []
        );
      })
      .catch((solicitudError) => {
        if (vigente) {
          setError(
            solicitudError?.message ||
              "Error al cargar el inicio."
          );
        }
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [intento]);

  const reintentar = () => {
    setError("");
    setCargando(true);
    setIntento((actual) => actual + 1);
  };

  const titulo = campo(contenidos, "titulo", "Bienvenido a Todo Balato");
  const eslogan = campo(contenidos, "eslogan", "Bueno, bonito y balato.");
  const tituloCategorias = campo(contenidos, "titulo_categorias", "Categorías");
  const tituloDestacados = campo(contenidos, "titulo_destacados", "Productos destacados");
  const bannerImagen = campo(contenidos, "banner_principal", "/logo-todo-balato.png");
  const bannerAlt = textoAlternativo(contenidos, "banner_principal", "Logo de Todo Balato");
  const bannerEnlace = campo(contenidos, "banner_enlace", "/catalogo");
  const rutaInterna = RUTAS_INTERNAS[bannerEnlace.split("?")[0]];

  const abrirBanner = (e) => {
    if (!rutaInterna) return;
    e.preventDefault();
    onNavegar(rutaInterna);
  };

  return (
    <>
      <section className="inicio-hero">
        {bannerImagen && (
          <a
            href={bannerEnlace}
            className="inicio-banner-enlace"
            onClick={abrirBanner}
            {...(!rutaInterna ? { target: "_blank", rel: "noopener noreferrer" } : {})}
          >
            <img src={bannerImagen} alt={bannerAlt} className="inicio-banner-img" />
          </a>
        )}
        <h1 className="titulo-marca">{titulo}</h1>
        <p>{eslogan}</p>
      </section>

      <h2 className="subtitulo">{tituloCategorias}</h2>

      <div className="categorias">
        {categorias.map((categoria) => (
          <button
            key={categoria.id}
            type="button"
            className="categoria-btn"
            onClick={() =>
              onNavegar("catalogo", categoria.id)
            }
          >
            {categoria.nombre}
          </button>
        ))}
      </div>

      <h2 className="subtitulo">{tituloDestacados}</h2>

      {cargando && (
        <p role="status">
          Cargando productos destacados...
        </p>
      )}

      {!cargando && error && (
        <div role="alert">
          <p>{error}</p>

          <button
            type="button"
            onClick={reintentar}
          >
            Reintentar
          </button>
        </div>
      )}

      {!cargando && !error && productos.length === 0 && (
        <p>No hay productos destacados disponibles.</p>
      )}

      {!cargando && !error && productos.length > 0 && (
        <div className="productos-grid">
          {productos.map((producto) => (
            <ProductCard
              key={producto.id}
              {...producto}
              onAgregarCarrito={onAgregar}
              onVerDetalle={onVerProducto}
            />
          ))}
        </div>
      )}
    </>
  );
}
