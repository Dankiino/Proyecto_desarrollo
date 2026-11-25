import { useState } from "react";
import { enviarMensajeContacto } from "../services/contacto";
import { campo } from "../services/contenidos";

const CAMPOS_INICIALES = {
  nombre: "",
  correo: "",
  mensaje: "",
};

const MAX_NOMBRE = 100;
const MAX_MENSAJE = 2000;
const REGEX_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validarFormulario(datos) {
  const errores = {};
  const nombre = datos.nombre.trim();
  const correo = datos.correo.trim();
  const mensaje = datos.mensaje.trim();

  if (!nombre) {
    errores.nombre = ["El nombre es obligatorio."];
  } else if (datos.nombre.length > MAX_NOMBRE) {
    errores.nombre = [`El nombre no puede superar los ${MAX_NOMBRE} caracteres.`];
  }

  if (!correo) {
    errores.correo = ["El correo electrónico es obligatorio."];
  } else if (!REGEX_CORREO.test(correo)) {
    errores.correo = ["Ingresa un correo electrónico válido."];
  }

  if (!mensaje) {
    errores.mensaje = ["El mensaje es obligatorio."];
  } else if (datos.mensaje.length > MAX_MENSAJE) {
    errores.mensaje = [`El mensaje no puede superar los ${MAX_MENSAJE} caracteres.`];
  }

  return errores;
}

function obtenerMensajeError(errorCampo) {
  if (!errorCampo) return "";
  return Array.isArray(errorCampo) ? errorCampo.join(" ") : String(errorCampo);
}

export default function Contacto({ contenidos }) {
  const [datos, setDatos] = useState(CAMPOS_INICIALES);
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [exito, setExito] = useState("");
  const [errorGeneral, setErrorGeneral] = useState("");

  const cambiarCampo = (evento) => {
    const { name, value } = evento.target;

    setDatos((actual) => ({
      ...actual,
      [name]: value,
    }));

    setErrores((actual) => {
      if (!actual[name]) return actual;
      const siguiente = { ...actual };
      delete siguiente[name];
      return siguiente;
    });

    setExito("");
    setErrorGeneral("");
  };

  const enviarMensaje = async (evento) => {
    evento.preventDefault();
    if (enviando) return;

    const erroresLocales = validarFormulario(datos);
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      setExito("");
      setErrorGeneral("Revisa los campos marcados antes de enviar.");
      return;
    }

    setEnviando(true);
    setErrores({});
    setExito("");
    setErrorGeneral("");

    const payload = {
      nombre: datos.nombre.trim(),
      correo: datos.correo.trim(),
      mensaje: datos.mensaje.trim(),
    };

    try {
      const respuesta = await enviarMensajeContacto(payload);
      if (respuesta?.status !== 201) {
        setErrorGeneral("No se pudo confirmar el envío del mensaje.");
        return;
      }

      setExito("Tu mensaje fue enviado correctamente.");
      setDatos({ ...CAMPOS_INICIALES });
    } catch (error) {
      if (error?.campos && typeof error.campos === "object") {
        setErrores(error.campos);
        setErrorGeneral("Revisa los campos marcados antes de enviar.");
      } else {
        setErrorGeneral(
          error?.message || "No fue posible enviar el mensaje. Intenta nuevamente."
        );
      }
    } finally {
      setEnviando(false);
    }
  };

  const msgNombre = obtenerMensajeError(errores.nombre);
  const msgCorreo = obtenerMensajeError(errores.correo);
  const msgMensaje = obtenerMensajeError(errores.mensaje);

  const titulo = campo(contenidos, "titulo", "Contáctanos");
  const introduccion = campo(
    contenidos,
    "introduccion",
    "¿Tienes alguna consulta sobre tus compras o nuestros productos? Escríbenos y te responderemos a la brevedad."
  );
  const correoContacto = campo(contenidos, "correo", "contacto@todobalato.cl");
  const telefonoContacto = campo(contenidos, "telefono", "+56 2 2890 4310");
  const horarioContacto = campo(
    contenidos,
    "horario",
    "Lunes a Viernes de 09:00 a 18:30 hrs · Sábados de 10:00 a 14:00 hrs"
  );

  return (
    <section className="contacto-pagina" aria-labelledby="titulo-contacto">
      <div className="contacto-contenedor">
        <header className="contacto-encabezado">
          <h1 id="titulo-contacto">{titulo}</h1>
          <p>{introduccion}</p>
        </header>

        <div className="contacto-layout">
          <aside className="contacto-info" aria-label="Datos de contacto">
            <h2>Canales de atención</h2>
            <dl className="contacto-datos">
              <div>
                <dt>Correo</dt>
                <dd>
                  <a href={`mailto:${correoContacto}`}>{correoContacto}</a>
                </dd>
              </div>
              <div>
                <dt>Teléfono</dt>
                <dd>
                  <a href={`tel:${telefonoContacto.replace(/\s+/g, "")}`}>
                    {telefonoContacto}
                  </a>
                </dd>
              </div>
              <div>
                <dt>Horario</dt>
                <dd>{horarioContacto}</dd>
              </div>
            </dl>
          </aside>

          <form className="contacto-formulario" onSubmit={enviarMensaje} noValidate>
            <div className="contacto-campo">
              <label htmlFor="contacto-nombre">Nombre</label>
              <input
                id="contacto-nombre"
                type="text"
                name="nombre"
                autoComplete="name"
                value={datos.nombre}
                onChange={cambiarCampo}
                maxLength={MAX_NOMBRE}
                required
                aria-invalid={Boolean(msgNombre)}
                aria-describedby={msgNombre ? "error-nombre" : "contador-nombre"}
              />
              <small id="contador-nombre" className="contacto-contador">
                {datos.nombre.length}/{MAX_NOMBRE} caracteres
              </small>
              {msgNombre && (
                <small id="error-nombre" role="alert" className="contacto-error-campo">
                  {msgNombre}
                </small>
              )}
            </div>

            <div className="contacto-campo">
              <label htmlFor="contacto-correo">Correo electrónico</label>
              <input
                id="contacto-correo"
                type="email"
                name="correo"
                autoComplete="email"
                value={datos.correo}
                onChange={cambiarCampo}
                required
                aria-invalid={Boolean(msgCorreo)}
                aria-describedby={msgCorreo ? "error-correo" : undefined}
              />
              {msgCorreo && (
                <small id="error-correo" role="alert" className="contacto-error-campo">
                  {msgCorreo}
                </small>
              )}
            </div>

            <div className="contacto-campo">
              <label htmlFor="contacto-mensaje">Mensaje</label>
              <textarea
                id="contacto-mensaje"
                name="mensaje"
                value={datos.mensaje}
                onChange={cambiarCampo}
                maxLength={MAX_MENSAJE}
                rows={5}
                required
                aria-invalid={Boolean(msgMensaje)}
                aria-describedby={msgMensaje ? "error-mensaje" : "contador-mensaje"}
              />
              <small id="contador-mensaje" className="contacto-contador">
                {datos.mensaje.length}/{MAX_MENSAJE} caracteres
              </small>
              {msgMensaje && (
                <small id="error-mensaje" role="alert" className="contacto-error-campo">
                  {msgMensaje}
                </small>
              )}
            </div>

            {errorGeneral && (
              <p role="alert" className="contacto-error">
                {errorGeneral}
              </p>
            )}

            {exito && (
              <p role="status" className="contacto-exito">
                {exito}
              </p>
            )}

            <button type="submit" disabled={enviando}>
              {enviando ? "Enviando..." : "Enviar mensaje"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}