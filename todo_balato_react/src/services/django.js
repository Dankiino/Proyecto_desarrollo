import {
  CATEGORIAS_INICIO_MOCK,
  CONTENIDOS_INICIO_MOCK,
  PRODUCTOS_INICIO_MOCK,
  TEMAS_MOCK,
  obtenerModoMockInicio,
  usaMockCatalogo,
  usaMockGestion,
} from "../data/mockInicio.js";

const gestionUrl = import.meta.env?.VITE_GESTION_API_URL || "http://127.0.0.1:8000/api";
const comercioUrl = import.meta.env?.VITE_COMERCIO_API_URL || "http://127.0.0.1:8001/api";
const catalogoUrl = import.meta.env?.VITE_CATALOGO_API_URL || "http://127.0.0.1:8002/api";

async function obtener(url, mensajeError, servicio = "El servicio") {
  let respuesta;
  try {
    respuesta = await fetch(url);
  } catch {
    throw new Error(mensajeError);
  }

  let resultado;
  try {
    resultado = await respuesta.json();
  } catch {
    throw new Error(`${servicio} devolvió una respuesta que no es JSON válido.`);
  }

  if (!respuesta.ok) {
    throw new Error(resultado?.detail || resultado?.error?.mensaje || mensajeError);
  }

  return resultado;
}

async function enviar(url, datos, token, idempotencyKey, metodo = "POST") {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;

  let respuesta;
  try {
    respuesta = await fetch(url, {
      method: metodo,
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

export const combinarCarrito = (items, token) => enviar(
  `${comercioUrl}/carrito/combinar`,
  { items },
  token,
);
export const guardarCantidad = (id, cantidad, token) => enviar(
  `${comercioUrl}/carrito/items/${encodeURIComponent(id)}`,
  { cantidad },
  token,
  undefined,
  "PUT",
);
export const quitarDelCarrito = (id, token) => enviar(
  `${comercioUrl}/carrito/items/${encodeURIComponent(id)}`,
  undefined,
  token,
  undefined,
  "DELETE",
);

export const obtenerCategoriasCatalogo = async () => {
  const modo = obtenerModoMockInicio();
  if (usaMockCatalogo(modo)) {
    if (modo === "error" || modo === "error_catalogo") {
      throw new Error("No se pudieron cargar las categorías del catálogo.");
    }
    if (modo === "vacio") return { results: [] };
    return CATEGORIAS_INICIO_MOCK;
  }
  return obtener(
    `${catalogoUrl}/categorias`,
    "No se pudieron cargar las categorías del catálogo.",
    "Catálogo",
  );
};

export const listarProductosCatalogo = async ({ page = 1, pageSize = 20, disponible = false } = {}) => {
  const modo = obtenerModoMockInicio();
  if (usaMockCatalogo(modo)) {
    if (modo === "error" || modo === "error_catalogo") {
      throw new Error("No se pudieron cargar los productos del catálogo.");
    }
    if (modo === "vacio") return { count: 0, page, page_size: pageSize, results: [] };
    const lista = disponible
      ? PRODUCTOS_INICIO_MOCK.results.filter((p) => p.disponible)
      : PRODUCTOS_INICIO_MOCK.results;
    return {
      ...PRODUCTOS_INICIO_MOCK,
      page,
      page_size: pageSize,
      results: lista.slice(0, pageSize),
    };
  }
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (disponible) params.set("disponible", "true");
  return obtener(
    `${catalogoUrl}/productos?${params.toString()}`,
    "No se pudieron cargar los productos del catálogo.",
    "Catálogo",
  );
};

export const obtenerProductoCatalogo = async (productoId) => {
  const modo = obtenerModoMockInicio();
  if (usaMockCatalogo(modo)) {
    if (modo === "error" || modo === "error_catalogo") {
      throw new Error("No se pudo cargar el producto.");
    }
    const encontrado = PRODUCTOS_INICIO_MOCK.results.find((p) => p.id === productoId);
    if (!encontrado) throw new Error("El producto no existe o no está disponible.");
    return {
      ...encontrado,
      descripcion: `Detalle de prueba para ${encontrado.nombre}.`,
      stock_disponible: 10,
      imagenes: encontrado.imagen_principal ? [encontrado.imagen_principal] : [],
      actualizado_en: new Date().toISOString(),
    };
  }
  return obtener(
    `${catalogoUrl}/productos/${encodeURIComponent(productoId)}`,
    "No se pudo cargar el producto.",
    "Catálogo",
  );
};

export const obtenerContenidosInicio = async () => {
  const modo = obtenerModoMockInicio();
  if (usaMockGestion(modo)) {
    if (modo === "error" || modo === "error_gestion") {
      throw new Error("No se pudieron cargar los contenidos de Inicio desde Gestión.");
    }
    if (modo === "vacio") return { pagina: "inicio", results: [] };
    return CONTENIDOS_INICIO_MOCK;
  }
  return obtener(
    `${gestionUrl}/contenidos/inicio`,
    "No se pudieron cargar los contenidos de Inicio desde Gestión.",
    "Gestión",
  );
};

export const obtenerTemaActivo = async () => {
  const modo = obtenerModoMockInicio();
  if (usaMockGestion(modo)) {
    if (modo === "error" || modo === "error_gestion") {
      throw new Error("No se pudo cargar el tema activo desde Gestión.");
    }
    if (modo === "tema_oscuro") return TEMAS_MOCK["balato-oscuro"];
    if (modo === "tema_clasico") return TEMAS_MOCK["balato-clasico"];
    return TEMAS_MOCK["balato-crema"];
  }
  return obtener(
    `${gestionUrl}/temas/activo`,
    "No se pudo cargar el tema activo desde Gestión.",
    "Gestión",
  );
};

