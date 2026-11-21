const gestionUrl = import.meta.env.VITE_GESTION_API_URL || "http://127.0.0.1:8000/api";
const comercioUrl = import.meta.env.VITE_COMERCIO_API_URL || "http://127.0.0.1:8001/api";
const catalogoUrl = import.meta.env.VITE_CATALOGO_API_URL || "http://127.0.0.1:8002/api";

async function enviar(url, datos, token, idempotencyKey) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;

  let respuesta;
  try {
    respuesta = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(datos),
    });
  } catch {
    throw new Error("No se pudo conectar con Django. Revisa que el servicio esté iniciado.");
  }

  let resultado = null;
  if (respuesta.status !== 204 && respuesta.status !== 205) {
    try {
      resultado = await respuesta.json();
    } catch {
      throw new Error("Django devolvió una respuesta que no es JSON válido.");
    }
  }

  if (!respuesta.ok) {
    const mensaje = resultado?.detail
      || resultado?.error?.mensaje
      || Object.values(resultado || {}).flat().join(" ")
      || "No se pudo completar la solicitud.";
    throw new Error(mensaje);
  }

  return resultado;
}

export const registro = (datos) => enviar(`${gestionUrl}/registro`, datos);
export const login = (datos) => enviar(`${gestionUrl}/login`, datos);
export const miUsuario = async (token) => {
  let respuesta;
  try {
    respuesta = await fetch(`${gestionUrl}/usuarios/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("No se pudo conectar con Django. Revisa que Gestión esté iniciado.");
  }

  const resultado = await respuesta.json();
  if (!respuesta.ok) throw new Error(resultado.detail || "No se pudo consultar la cuenta.");
  return resultado;
};
export const logout = (token, refresh) => enviar(
  `${gestionUrl}/logout`,
  { refresh },
  token,
);
export const calcularCarrito = (items) => enviar(`${comercioUrl}/carrito/calcular`, { items });
export const crearOrden = (items, total, token, idempotencyKey) => enviar(
  `${comercioUrl}/checkout`,
  { items, total_esperado: total },
  token,
  idempotencyKey,
);
// CATÁLOGO

export const obtenerProductos = async (pagina = 1, limite = 20, categoriaId = "") => {
  const parametros = new URLSearchParams({
    page: pagina,
    limit: limite,
  });

  if (categoriaId) {
    parametros.append("categoria_id", categoriaId);
  }

  return consultar(`${catalogoUrl}/productos?${parametros.toString()}`);
};

export const obtenerCategorias = async () => {
  return consultar(`${catalogoUrl}/categorias`);
};

export const obtenerProducto = async (id) => {
  return consultar(`${catalogoUrl}/productos/${encodeURIComponent(id)}`);
};

// GET para consultar los servicios
async function consultar(url) {
  let respuesta;

  try {
    respuesta = await fetch(url);
  } catch {
    throw new Error("No se pudo conectar con el servicio de Catálogo.");
  }

  let resultado;

  try {
    resultado = await respuesta.json();
  } catch {
    throw new Error("El servicio de Catálogo devolvió una respuesta inválida.");
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.error?.mensaje ||
      resultado?.detail ||
      "No se pudieron obtener los datos del catálogo."
    );
  }

  return resultado;
}