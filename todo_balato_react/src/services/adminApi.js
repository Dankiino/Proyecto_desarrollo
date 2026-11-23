
const GESTION_API =
    import.meta.env.VITE_GESTION_API_URL ||
    "http://127.0.0.1:8000/api";

const CATALOGO_API =
    import.meta.env.VITE_CATALOGO_API_URL ||
    "http://127.0.0.1:8002/api";

export async function solicitudAdmin(
    ruta,
    { method = "GET", token, datos } = {}
) {
    if (!token) {
        throw new Error("Debes iniciar sesión como administrador.");
    }

    let respuesta;

    try {
        respuesta = await fetch(`${CATALOGO_API}${ruta}`, {
            method,
            headers: {
                Authorization: `Bearer ${token}`,
                ...(datos ? { "Content-Type": "application/json" } : {}),
            },
            ...(datos ? { body: JSON.stringify(datos) } : {}),
        });
    } catch {
        throw new Error("No se pudo conectar con el servicio Catálogo.");
    }

    const resultado = await respuesta.json().catch(() => null);

    if (!respuesta.ok) {
        const campos = resultado?.error?.campos || resultado?.campos;

        const detalle = campos
            ? Object.entries(campos)
                .map(([campo, errores]) =>
                    `${campo}: ${Array.isArray(errores) ? errores.join(", ") : errores}`
                )
                .join(". ")
            : "";

        throw new Error(
            detalle ||
            resultado?.error?.mensaje ||
            resultado?.detail ||
            "No se pudo completar la operación."
        );
    }

    return resultado;
}

export async function autenticarAdmin(correo, password) {
    const respuesta = await fetch(`${GESTION_API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo, password }),
    });

    const tokens = await respuesta.json().catch(() => null);

    if (!respuesta.ok) {
        throw new Error(tokens?.detail || "No se pudo iniciar sesión.");
    }

    const usuarioRespuesta = await fetch(
        `${GESTION_API}/usuarios/me`,
        {
            headers: { Authorization: `Bearer ${tokens.access}` },
        }
    );

    const usuario = await usuarioRespuesta.json().catch(() => null);

    if (!usuarioRespuesta.ok) {
        throw new Error("No se pudo comprobar la cuenta.");
    }

    if (usuario.rol !== "ADMIN" || usuario.estado !== "ACTIVO") {
        throw new Error("Esta cuenta no tiene acceso administrativo.");
    }

    return { tokens, usuario };
}

export const listarProductosAdmin = (token) =>
    solicitudAdmin("/admin/productos", { token });

export const crearProductoAdmin = (token, datos) =>
    solicitudAdmin("/admin/productos", {
        method: "POST",
        token,
        datos,
    });

export const editarProductoAdmin = (token, id, datos) =>
    solicitudAdmin(`/admin/productos/${encodeURIComponent(id)}`, {
        method: "PATCH",
        token,
        datos,
    });

export const desactivarProductoAdmin = (token, id) =>
    solicitudAdmin(
        `/admin/productos/${encodeURIComponent(id)}`,
        {
            method: "PATCH",
            token,
            datos: { activo: false },
        }
    );

export const listarCategoriasAdmin = (token) =>
    solicitudAdmin("/admin/categorias", { token });

export const crearCategoriaAdmin = (token, datos) =>
    solicitudAdmin("/admin/categorias", {
        method: "POST",
        token,
        datos,
    });

export const editarCategoriaAdmin = (token, id, datos) =>
    solicitudAdmin(`/admin/categorias/${encodeURIComponent(id)}`, {
        method: "PATCH",
        token,
        datos,
    });



/* =====================================
   MENSAJES DE CONTACTO - GESTIÓN
   ===================================== */

async function solicitudContacto(ruta, token) {
    if (!token) {
        throw new Error("Debes iniciar sesión como administrador.");
    }

    let respuesta;

    try {
        respuesta = await fetch(`${GESTION_API}${ruta}`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
    } catch {
        throw new Error(
            "No se pudo conectar con el servicio Gestión."
        );
    }

    const resultado = await respuesta.json().catch(() => null);

    if (!respuesta.ok) {
        if (respuesta.status === 401) {
            throw new Error(
                "Tu sesión no es válida o ha expirado."
            );
        }

        if (respuesta.status === 403) {
            throw new Error(
                "Esta cuenta no está autorizada para consultar mensajes de contacto."
            );
        }

        throw new Error(
            resultado?.detail ||
            "No fue posible consultar los mensajes."
        );
    }

    return resultado;
}

export const listarMensajesContacto = (token) =>
    solicitudContacto("/admin/contacto/", token);

export const obtenerMensajeContacto = (token, id) =>
    solicitudContacto(
        `/admin/contacto/${encodeURIComponent(id)}/`,
        token
    );
