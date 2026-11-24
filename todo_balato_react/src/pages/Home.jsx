import { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import {
  listarProductosCatalogo,
  obtenerCategoriasCatalogo,
  obtenerContenidosInicio,
} from "../services/django";

const RUTAS_INTERNAS = {
  "/": "inicio",
  "/inicio": "inicio",
  "/catalogo": "catalogo",
  "/quienes-somos": "quienes-somos",
  "/carrito": "carrito",
  "/cuenta": "cuenta",
  "/pago": "pago",
};

function normalizarContenidos(datos) {
  if (!datos || typeof datos !== "object") return null;

  const lista = Array.isArray(datos)
    ? datos
    : Array.isArray(datos.results)
      ? datos.results
      : Array.isArray(datos.contenidos)
        ? datos.contenidos
        : null;

  const mapa = {};
  if (lista) {
    for (const item of lista) {
      if (item && typeof item.clave === "string") {
        mapa[item.clave] = {
          valor: typeof item.valor === "string" ? item.valor : "",
          texto_alternativo: typeof item.texto_alternativo === "string" ? item.texto_alternativo : "",
        };
      }
    }
    return Object.keys(mapa).length > 0 ? mapa : {};
  }

  const origen = datos.contenidos && typeof datos.contenidos === "object" ? datos.contenidos : datos;
  const clavesConocidas = [
    "titulo",
    "eslogan",
    "titulo_categorias",
    "titulo_destacados",
    "banner_principal",
    "banner_enlace",
  ];
  for (const clave of clavesConocidas) {
    const entrada = origen[clave];
    if (typeof entrada === "string") {
      mapa[clave] = { valor: entrada, texto_alternativo: "" };
    } else if (entrada && typeof entrada === "object" && typeof entrada.valor === "string") {
      mapa[clave] = {
        valor: entrada.valor,
        texto_alternativo: typeof entrada.texto_alternativo === "string" ? entrada.texto_alternativo : "",
      };
    }
  }
  return Object.keys(mapa).length > 0 ? mapa : {};
}

function resolverDestinoBanner(enlace) {
  const limpio = (enlace || "").trim();
  if (!limpio) return null;
  if (/^https?:\/\//i.test(limpio)) {
    return { tipo: "externo", href: limpio };
  }
  const [rutaBase, query = ""] = limpio.split("?");
  const pagina = RUTAS_INTERNAS[rutaBase.toLowerCase()];
  if (!pagina) return null;
  const categoria = new URLSearchParams(query).get("categoria") || "";
  return { tipo: "interno", pagina, categoria };
}

export default function Home({
  onNavegar,
  onAgregar,
  onVerProducto,
  errorTema = "",
  onReintentarTema,
}) {
  const [contenidos, setContenidos] = useState(null);
  const [cargandoContenidos, setCargandoContenidos] = useState(true);
  const [errorContenidos, setErrorContenidos] = useState("");

  const [categorias, setCategorias] = useState([]);
  const [cargandoCategorias, setCargandoCategorias] = useState(true);
  const [errorCategorias, setErrorCategorias] = useState("");

  const [productos, setProductos] = useState([]);
  const [cargandoProductos, setCargandoProductos] = useState(true);
  const [errorProductos, setErrorProductos] = useState("");

  const [intentoContenidos, setIntentoContenidos] = useState(0);
  const [intentoCategorias, setIntentoCategorias] = useState(0);
  const [intentoProductos, setIntentoProductos] = useState(0);

  useEffect(() => {
    let vigente = true;
    obtenerContenidosInicio()
      .then((datos) => {
        if (!vigente) return;
        const normalizados = normalizarContenidos(datos);
        if (!normalizados) {
          setErrorContenidos("Gestión devolvió un formato inválido para los contenidos de Inicio.");
          setContenidos(null);
          return;
        }
        setContenidos(normalizados);
      })
      .catch((solicitudError) => {
        if (!vigente) return;
        setErrorContenidos(
          solicitudError?.message || "No se pudieron cargar los contenidos de Inicio desde Gestión.",
        );
        setContenidos(null);
      })
      .finally(() => {
        if (vigente) setCargandoContenidos(false);
      });

    return () => {
      vigente = false;
    };
  }, [intentoContenidos]);

  useEffect(() => {
    let vigente = true;
    obtenerCategoriasCatalogo()
      .then((catsData) => {
        if (!vigente) return;
        if (!Array.isArray(catsData?.results)) {
          setErrorCategorias("Catálogo devolvió un formato inválido al cargar las categorías.");
          setCategorias([]);
          return;
        }
        setCategorias(catsData.results);
      })
      .catch((solicitudError) => {
        if (!vigente) return;
        setErrorCategorias(solicitudError?.message || "No se pudieron cargar las categorías.");
        setCategorias([]);
      })
      .finally(() => {
        if (vigente) setCargandoCategorias(false);
      });

    return () => {
      vigente = false;
    };
  }, [intentoCategorias]);

  useEffect(() => {
    let vigente = true;
    listarProductosCatalogo({ page: 1, pageSize: 4, disponible: true })
      .then((prodsData) => {
        if (!vigente) return;
        if (!Array.isArray(prodsData?.results)) {
          setErrorProductos("Catálogo devolvió un formato inválido al cargar los productos.");
          setProductos([]);
          return;
        }
        const disponibles = prodsData.results
          .filter((producto) => producto.disponible !== false)
          .slice(0, 4);
        setProductos(disponibles);
      })
      .catch((solicitudError) => {
        if (!vigente) return;
        setErrorProductos(
          solicitudError?.message || "No se pudieron cargar los productos destacados.",
        );
        setProductos([]);
      })
      .finally(() => {
        if (vigente) setCargandoProductos(false);
      });

    return () => {
      vigente = false;
    };
  }, [intentoProductos]);

  const reintentarContenidos = () => {
    setErrorContenidos("");
    setCargandoContenidos(true);
    setIntentoContenidos((actual) => actual + 1);
    if (errorTema && onReintentarTema) onReintentarTema();
  };

  const reintentarCategorias = () => {
    setErrorCategorias("");
    setCargandoCategorias(true);
    setIntentoCategorias((actual) => actual + 1);
  };

  const reintentarProductos = () => {
    setErrorProductos("");
    setCargandoProductos(true);
    setIntentoProductos((actual) => actual + 1);
  };

  const sinContenidos = !cargandoContenidos && !errorContenidos
    && contenidos && Object.keys(contenidos).length === 0;

  const titulo = contenidos?.titulo?.valor || "Bienvenido a Todo Balato";
  const eslogan = contenidos?.eslogan?.valor || "";
  const tituloCategorias = contenidos?.titulo_categorias?.valor || "Categorías";
  const tituloDestacados = contenidos?.titulo_destacados?.valor || "Productos destacados";
  const bannerUrl = contenidos?.banner_principal?.valor || "";
  const bannerAlt = contenidos?.banner_principal?.texto_alternativo || titulo;
  const destinoBanner = resolverDestinoBanner(contenidos?.banner_enlace?.valor);

  const errorGestion = errorContenidos || errorTema;

  return (
    <>
      <section className="inicio-hero" aria-labelledby="inicio-titulo">
        <h1 id="inicio-titulo" className="titulo-marca">{titulo}</h1>

        {cargandoContenidos && (
          <p role="status" className="inicio-estado">Cargando contenidos de inicio...</p>
        )}

        {!cargandoContenidos && errorGestion && (
          <div role="alert" className="inicio-alerta">
            <p>{errorGestion}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={reintentarContenidos}>
              Reintentar
            </button>
          </div>
        )}

        {sinContenidos && (
          <p role="status" className="inicio-estado">
            No hay contenidos administrables publicados para Inicio en este momento.
          </p>
        )}

        {!cargandoContenidos && eslogan && <p className="inicio-eslogan">{eslogan}</p>}

        {!cargandoContenidos && bannerUrl && (
          <div className="inicio-banner">
            {destinoBanner?.tipo === "interno" ? (
              <button
                type="button"
                className="inicio-banner-btn"
                aria-label={`${bannerAlt} — Ir a ${destinoBanner.pagina}`}
                onClick={() => onNavegar(destinoBanner.pagina, destinoBanner.categoria)}
              >
                <img src={bannerUrl} alt={bannerAlt} className="inicio-banner-img" />
              </button>
            ) : destinoBanner?.tipo === "externo" ? (
              <a
                href={destinoBanner.href}
                target="_blank"
                rel="noopener noreferrer"
                className="inicio-banner-btn"
                aria-label={bannerAlt}
              >
                <img src={bannerUrl} alt={bannerAlt} className="inicio-banner-img" />
              </a>
            ) : (
              <img src={bannerUrl} alt={bannerAlt} className="inicio-banner-img" />
            )}
          </div>
        )}
      </section>

      <section aria-labelledby="inicio-categorias">
        <h2 id="inicio-categorias" className="subtitulo">{tituloCategorias}</h2>

        {cargandoCategorias && (
          <p role="status" className="inicio-estado">Cargando categorías...</p>
        )}

        {!cargandoCategorias && errorCategorias && (
          <div role="alert" className="inicio-alerta">
            <p>{errorCategorias}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={reintentarCategorias}>
              Reintentar
            </button>
          </div>
        )}

        {!cargandoCategorias && !errorCategorias && categorias.length === 0 && (
          <p role="status" className="inicio-estado">
            No hay categorías activas disponibles en este momento.
          </p>
        )}

        {!cargandoCategorias && !errorCategorias && categorias.length > 0 && (
          <div className="categorias">
            {categorias.map((categoria) => (
              <button
                key={categoria.id}
                type="button"
                className="categoria-btn"
                onClick={() => onNavegar("catalogo", categoria.id)}
              >
                {categoria.nombre}
              </button>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="inicio-destacados">
        <h2 id="inicio-destacados" className="subtitulo">{tituloDestacados}</h2>

        {cargandoProductos && (
          <p role="status" className="inicio-estado">Cargando productos destacados...</p>
        )}

        {!cargandoProductos && errorProductos && (
          <div role="alert" className="inicio-alerta">
            <p>{errorProductos}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={reintentarProductos}>
              Reintentar
            </button>
          </div>
        )}

        {!cargandoProductos && !errorProductos && productos.length === 0 && (
          <p role="status" className="inicio-estado">
            No hay productos disponibles para mostrar en este momento.
          </p>
        )}

        {!cargandoProductos && !errorProductos && productos.length > 0 && (
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
      </section>
    </>
  );
}
