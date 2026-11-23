
import { useState } from "react";

const CAMPOS_INICIALES = {
    nombre: "",
    correo: "",
    mensaje: "",
};

export default function Contacto() {
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

        setErrores((actual) => ({
            ...actual,
            [name]: undefined,
        }));

        setExito("");
        setErrorGeneral("");
    };

    const enviarMensaje = async (evento) => {
        evento.preventDefault();

        if (enviando) return;

        setEnviando(true);
        setErrores({});
        setExito("");
        setErrorGeneral("");

        try {
            const respuesta = await fetch(
                "http://127.0.0.1:8000/api/contacto/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(datos),
                }
            );

            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                if (respuesta.status === 400) {
                    setErrores(resultado);
                } else {
                    setErrorGeneral(
                        "No fue posible enviar el mensaje. Intenta nuevamente."
                    );
                }
                return;
            }

            if (respuesta.status !== 201) {
                setErrorGeneral(
                    "No se pudo confirmar el envío del mensaje."
                );
                return;
            }

            setExito("Tu mensaje fue enviado correctamente.");
            setDatos({ ...CAMPOS_INICIALES });
        } catch {
            setErrorGeneral(
                "No fue posible conectar con el servidor. Intenta nuevamente."
            );
        } finally {
            setEnviando(false);
        }
    };

    return (
        <section className="contacto-pagina">
            <div className="contacto-contenedor">
                <h1>Contáctanos</h1>
                <p>
                    ¿Tienes alguna consulta? Escríbenos y nos pondremos
                    en contacto contigo.
                </p>

                <form onSubmit={enviarMensaje} noValidate>
                    <div className="contacto-campo">
                        <label htmlFor="contacto-nombre">Nombre</label>
                        <input
                            id="contacto-nombre"
                            type="text"
                            name="nombre"
                            value={datos.nombre}
                            onChange={cambiarCampo}
                            maxLength={100}
                            required
                            aria-invalid={Boolean(errores.nombre)}
                        />
                        {errores.nombre && (
                            <small role="alert">{errores.nombre.join(" ")}</small>
                        )}
                    </div>

                    <div className="contacto-campo">
                        <label htmlFor="contacto-correo">
                            Correo electrónico
                        </label>
                        <input
                            id="contacto-correo"
                            type="email"
                            name="correo"
                            value={datos.correo}
                            onChange={cambiarCampo}
                            required
                            aria-invalid={Boolean(errores.correo)}
                        />
                        {errores.correo && (
                            <small role="alert">{errores.correo.join(" ")}</small>
                        )}
                    </div>

                    <div className="contacto-campo">
                        <label htmlFor="contacto-mensaje">Mensaje</label>
                        <textarea
                            id="contacto-mensaje"
                            name="mensaje"
                            value={datos.mensaje}
                            onChange={cambiarCampo}
                            maxLength={2000}
                            rows={6}
                            required
                            aria-invalid={Boolean(errores.mensaje)}
                        />
                        {errores.mensaje && (
                            <small role="alert">{errores.mensaje.join(" ")}</small>
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
        </section>
    );
}
