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

async function leerCatalogo(ruta) {
  let respuesta;
  try {
    respuesta = await fetch(`${catalogoUrl}${ruta}`);
  } catch {
    throw new Error("No se pudo conectar con el servicio de catálogo (puerto 8002).");
  }

  let resultado = null;
  try {
    resultado = await respuesta.json();
  } catch {
    throw new Error("El servicio de catálogo devolvió una respuesta no válida.");
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.error?.mensaje || resultado?.detail || "No se pudo cargar el catálogo."
    );
  }

  return resultado;
}

export const obtenerCategoriasCatalogo = () => leerCatalogo("/categorias");

export const listarProductosCatalogo = ({ page = 1, pageSize = 20, categoria = "", orden = "recientes" } = {}) => {
  const safePageSize = Math.min(Math.max(Number(pageSize) || 20, 1), 50);
  const safePage = Math.max(Number(page) || 1, 1);
  const params = new URLSearchParams({
    page: String(safePage),
    page_size: String(safePageSize),
    orden,
  });
  if (categoria) params.set("categoria", categoria);
  return leerCatalogo(`/productos?${params.toString()}`);
};

export const obtenerProductoCatalogo = (productoId) =>
  leerCatalogo(`/productos/${encodeURIComponent(productoId)}`);