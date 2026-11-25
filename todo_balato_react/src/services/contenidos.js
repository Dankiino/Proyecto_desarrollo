const GESTION_API =
  import.meta.env.VITE_GESTION_API_URL || "http://127.0.0.1:8000/api";

/** Error con el código HTTP y los errores por campo devueltos por Django. */
export class ErrorApi extends Error {
  constructor(mensaje, { status = 0, campos = null } = {}) {
    super(mensaje);
    this.status = status;
    this.campos = campos;
  }
}

async function solicitar(ruta, { method = "GET", token, datos } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (datos) headers["Content-Type"] = "application/json";

  let respuesta;
  try {
    respuesta = await fetch(`${GESTION_API}${ruta}`, {
      method,
      headers,
      ...(datos ? { body: JSON.stringify(datos) } : {}),
    });
  } catch {
    throw new ErrorApi("No se pudo conectar con el servicio Gestión.");
  }

  const resultado = await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    const { status } = respuesta;
    let mensaje = resultado?.detail || "No se pudo completar la operación.";
    if (status === 401) mensaje = "Tu sesión no es válida o ha expirado. Vuelve a ingresar.";
    if (status === 403) mensaje = "Esta cuenta no está autorizada para administrar contenidos.";
    throw new ErrorApi(mensaje, { status, campos: resultado?.campos || null });
  }

  return resultado;
}

/** Contenidos y tema activo que muestran las páginas públicas. */
export const obtenerContenidosPublicos = () => solicitar("/contenidos");

export const obtenerContenidosAdmin = (token) =>
  solicitar("/admin/contenidos", { token });

export const guardarContenidosAdmin = (token, contenidos) =>
  solicitar("/admin/contenidos", { method: "PATCH", token, datos: { contenidos } });

export const activarTemaAdmin = (token, temaId) =>
  solicitar("/admin/tema-activo", { method: "PUT", token, datos: { tema_id: temaId } });

/** Lee `pagina.clave` de los contenidos públicos con un valor por defecto. */
export function campo(paginaDatos, clave, porDefecto = "") {
  return paginaDatos?.[clave]?.valor || porDefecto;
}

export function textoAlternativo(paginaDatos, clave, porDefecto = "") {
  return paginaDatos?.[clave]?.texto_alternativo || porDefecto;
}
