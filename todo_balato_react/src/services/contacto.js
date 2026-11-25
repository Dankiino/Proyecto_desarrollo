const USAR_MOCK_CONTACTO = import.meta.env.VITE_CONTACTO_REAL !== "true";

function simularRespuestaMock(payload) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const texto = `${payload.nombre} ${payload.correo} ${payload.mensaje}`.toLowerCase();
      if (texto.includes("error-test")) {
        reject(new Error("No fue posible enviar el mensaje. Intenta nuevamente."));
        return;
      }

      resolve({
        status: 201,
        data: {
          recibido: true,
          modo: "mock",
          creado_en: new Date().toISOString(),
        },
      });
    }, 650);
  });
}

export async function enviarMensajeContacto(payload) {
  if (USAR_MOCK_CONTACTO) {
    return simularRespuestaMock(payload);
  }

  const baseUrl =
    import.meta.env.VITE_API_GESTION_URL ||
    import.meta.env.VITE_GESTION_API_URL ||
    "http://127.0.0.1:8000/api";

  const respuesta = await fetch(`${baseUrl}/contacto/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const cuerpo = await respuesta.json().catch(() => ({}));

  if (respuesta.status === 400) {
    const errorValidacion = new Error("Revisa los campos marcados antes de enviar.");
    errorValidacion.campos = cuerpo;
    throw errorValidacion;
  }

  if (!respuesta.ok || respuesta.status !== 201) {
    throw new Error(cuerpo?.detail || "No se pudo confirmar el envío del mensaje.");
  }

  return { status: respuesta.status, data: cuerpo };
}