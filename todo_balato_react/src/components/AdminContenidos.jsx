import { useEffect, useState } from "react";
import {
  activarTemaAdmin,
  guardarContenidosAdmin,
  obtenerContenidosAdmin,
} from "../services/contenidos";

const PAGINAS = [
  ["inicio", "Inicio"],
  ["contacto", "Contacto"],
  ["quienes-somos", "Quiénes somos"],
];

const ETIQUETAS = {
  "inicio.titulo": "Título principal",
  "inicio.eslogan": "Eslogan",
  "inicio.titulo_categorias": "Título de la sección Categorías",
  "inicio.titulo_destacados": "Título de la sección Destacados",
  "inicio.banner_principal": "Banner principal (imagen)",
  "inicio.banner_enlace": "Enlace del banner",
  "contacto.titulo": "Título",
  "contacto.introduccion": "Texto de introducción",
  "contacto.correo": "Correo de atención",
  "contacto.telefono": "Teléfono",
  "contacto.horario": "Horario de atención",
  "quienes-somos.titulo": "Título",
  "quienes-somos.texto": "Texto principal",
  "quienes-somos.imagen": "Imagen",
};

const llave = (c) => `${c.pagina}.${c.clave}`;

const unirErrores = (errores) =>
  Array.isArray(errores) ? errores.join(" ") : String(errores || "");

export default function AdminContenidos({ token, onSesionVencida }) {
  const [datos, setDatos] = useState(null);
  const [pagina, setPagina] = useState("inicio");
  const [borrador, setBorrador] = useState({});
  const [errores, setErrores] = useState({});
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState("");
  const [error, setError] = useState("");

  const manejarError = (e) => {
    if (e.status === 401 || e.status === 403) {
      onSesionVencida(e.message);
      return;
    }
    setError(e.message);
  };

  const recibir = (respuesta) => {
    setDatos(respuesta);
    setBorrador(
      Object.fromEntries(
        respuesta.contenidos.map((c) => [
          llave(c),
          { valor: c.valor, texto_alternativo: c.texto_alternativo },
        ])
      )
    );
  };

  useEffect(() => {
    let vigente = true;
    obtenerContenidosAdmin(token)
      .then((r) => vigente && recibir(r))
      .catch((e) => vigente && manejarError(e))
      .finally(() => vigente && setCargando(false));
    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const cambiar = (k, campo, valor) => {
    setBorrador((b) => ({ ...b, [k]: { ...b[k], [campo]: valor } }));
    setErrores((actual) => {
      if (!actual[k]?.[campo]) return actual;
      const siguiente = { ...actual, [k]: { ...actual[k] } };
      delete siguiente[k][campo];
      return siguiente;
    });
    setAviso("");
  };

  const camposPagina = (datos?.contenidos || []).filter((c) => c.pagina === pagina);

  const guardar = async (e) => {
    e.preventDefault();
    if (guardando) return;
    setAviso("");
    setError("");

    const cambios = camposPagina
      .filter((c) => {
        const b = borrador[llave(c)];
        return b.valor !== c.valor || b.texto_alternativo !== c.texto_alternativo;
      })
      .map((c) => ({ pagina: c.pagina, clave: c.clave, ...borrador[llave(c)] }));

    if (cambios.length === 0) {
      setAviso("No hay cambios por guardar en esta página.");
      return;
    }

    setGuardando(true);
    try {
      const respuesta = await guardarContenidosAdmin(token, cambios);
      const anteriores = borrador;
      recibir(respuesta);
      setBorrador((nuevo) => {
        const mezcla = { ...nuevo };
        for (const c of respuesta.contenidos) {
          if (c.pagina !== pagina && anteriores[llave(c)]) mezcla[llave(c)] = anteriores[llave(c)];
        }
        return mezcla;
      });
      setErrores({});
      setAviso("Cambios guardados. Ya se muestran en el sitio público.");
    } catch (e2) {
      if (e2.campos) {
        setErrores(e2.campos);
        setError("Revisa los campos marcados. No se guardó ningún cambio de esta página.");
      } else {
        manejarError(e2);
      }
    } finally {
      setGuardando(false);
    }
  };

  const elegirTema = async (temaId) => {
    if (guardando || temaId === datos.tema_activo) return;
    setAviso("");
    setError("");
    setGuardando(true);
    try {
      await activarTemaAdmin(token, temaId);
      setDatos((d) => ({
        ...d,
        tema_activo: temaId,
        temas: d.temas.map((t) => ({ ...t, activo: t.id === temaId })),
      }));
      setAviso("Tema actualizado. Recarga el sitio público para verlo.");
    } catch (e) {
      if (e.campos?.tema_id) setError(unirErrores(e.campos.tema_id));
      else manejarError(e);
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) return <p role="status">Cargando contenidos...</p>;
  if (!datos) return error ? <p role="alert" className="admin-error">{error}</p> : null;

  return (
    <div className="admin-contenidos">
      {aviso && <p role="status" className="admin-exito">{aviso}</p>}
      {error && <p role="alert" className="admin-error">{error}</p>}

      <h2>Tema visual del sitio</h2>
      <p>Elige uno de los cuatro temas aprobados.</p>
      <div className="admin-temas" role="radiogroup" aria-label="Tema activo">
        {datos.temas.map((t) => (
          <button
            key={t.id}
            type="button"
            role="radio"
            aria-checked={t.id === datos.tema_activo}
            className={`admin-tema ${t.id === datos.tema_activo ? "seleccionado" : ""}`}
            disabled={guardando}
            onClick={() => elegirTema(t.id)}
            style={{ background: t.color_fondo, color: t.color_texto }}
          >
            <span className="admin-tema-colores" aria-hidden="true">
              {[t.color_primario, t.color_secundario, t.color_acento].map((c) => (
                <span key={c} style={{ background: c }} />
              ))}
            </span>
            <strong>{t.nombre}</strong>
            {t.id === datos.tema_activo && <small>Activo</small>}
          </button>
        ))}
      </div>

      <h2>Contenidos de las páginas</h2>
      <div className="admin-pestanas">
        {PAGINAS.map(([id, nombre]) => (
          <button
            key={id}
            type="button"
            aria-pressed={pagina === id}
            onClick={() => {
              setPagina(id);
              setAviso("");
              setError("");
            }}
          >
            {nombre}
          </button>
        ))}
      </div>

      <form className="admin-form" onSubmit={guardar} noValidate>
        {camposPagina.length === 0 && (
          <p>Esta página no tiene campos editables. Ejecuta «cargar_datos_iniciales» en Gestión.</p>
        )}

        {camposPagina.map((c) => {
          const k = llave(c);
          const b = borrador[k] || { valor: "", texto_alternativo: "" };
          const err = errores[k] || {};
          const idValor = `campo-${k}`;
          const largo = c.tipo === "texto" && (c.valor.length > 80 || c.clave === "texto");
          return (
            <fieldset key={k} className="admin-campo-contenido">
              <legend>
                {ETIQUETAS[k] || c.clave} <small>({c.tipo})</small>
              </legend>

              <label htmlFor={idValor}>
                {c.tipo === "texto" ? "Texto" : c.tipo === "imagen" ? "URL o ruta de la imagen" : "URL o ruta del enlace"}
              </label>
              {largo ? (
                <textarea
                  id={idValor}
                  rows={5}
                  value={b.valor}
                  aria-invalid={Boolean(err.valor)}
                  onChange={(e) => cambiar(k, "valor", e.target.value)}
                />
              ) : (
                <input
                  id={idValor}
                  type={c.tipo === "texto" ? "text" : "url"}
                  value={b.valor}
                  aria-invalid={Boolean(err.valor)}
                  onChange={(e) => cambiar(k, "valor", e.target.value)}
                />
              )}
              {err.valor && <small role="alert" className="admin-error-campo">{unirErrores(err.valor)}</small>}
              {err.clave && <small role="alert" className="admin-error-campo">{unirErrores(err.clave)}</small>}

              {c.tipo === "imagen" && (
                <>
                  <label htmlFor={`${idValor}-alt`}>Texto alternativo</label>
                  <input
                    id={`${idValor}-alt`}
                    value={b.texto_alternativo}
                    aria-invalid={Boolean(err.texto_alternativo)}
                    onChange={(e) => cambiar(k, "texto_alternativo", e.target.value)}
                  />
                  {err.texto_alternativo && (
                    <small role="alert" className="admin-error-campo">
                      {unirErrores(err.texto_alternativo)}
                    </small>
                  )}
                  {b.valor && (
                    <img className="admin-vista-previa" src={b.valor} alt={b.texto_alternativo} />
                  )}
                </>
              )}

              {c.actualizado_por && (
                <small className="admin-meta">
                  Última edición: {new Date(c.actualizado_en).toLocaleString("es-CL")} por {c.actualizado_por}
                </small>
              )}
            </fieldset>
          );
        })}

        {camposPagina.length > 0 && (
          <button type="submit" disabled={guardando}>
            {guardando ? "Guardando..." : "Guardar cambios de la página"}
          </button>
        )}
      </form>
    </div>
  );
}
