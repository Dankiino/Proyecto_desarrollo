
const catalogoUrl =
    import.meta.env.VITE_CATALOGO_API_URL ||
    "http://127.0.0.1:8002/api";

export async function obtenerProductos({
    categoria = "",
    buscar = "",
    pagina = 1,
    tamano = 100,
} = {}) {
    const parametros = new URLSearchParams({
        pagina: String(pagina),
        tamano: String(tamano),
    });

    if (categoria) parametros.set("categoria", categoria);
    if (buscar.trim()) parametros.set("buscar", buscar.trim());

    let respuesta;

    try {
        respuesta = await fetch(
            `${catalogoUrl}/productos?${parametros.toString()}`
        );
    } catch {
        throw new Error("No se pudo conectar con el servicio de Catálogo.");
    }

    if (!respuesta.ok) {
        throw new Error(`Error al obtener productos (${respuesta.status}).`);
    }

    return respuesta.json();
}
