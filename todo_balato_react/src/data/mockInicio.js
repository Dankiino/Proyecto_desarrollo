// Respuestas de prueba para avanzar y validar Inicio mientras Gestión (DEA-35)
// o Catálogo no estén levantados. Respetan los contratos de DEA-34 y DEA-37/DEA-35.

export const CATEGORIAS_INICIO_MOCK = {
  results: [
    { id: "cocina", nombre: "Cocina" },
    { id: "hogar", nombre: "Hogar" },
    { id: "accesorios", nombre: "Accesorios" },
    { id: "oficina", nombre: "Oficina" },
  ],
};

export const PRODUCTOS_INICIO_MOCK = {
  count: 4,
  page: 1,
  page_size: 4,
  results: [
    {
      id: "prod_0001",
      nombre: "Set de 6 vasos de vidrio",
      imagen_principal: {
        url: "/logo-todo-balato.png",
        texto_alternativo: "Set de 6 vasos de vidrio",
      },
      precio: 3990,
      moneda: "CLP",
      disponible: true,
      categorias: [{ id: "cocina", nombre: "Cocina" }],
    },
    {
      id: "prod_0002",
      nombre: "Organizador plegable multiuso",
      imagen_principal: {
        url: "/logo-todo-balato.png",
        texto_alternativo: "Organizador plegable multiuso",
      },
      precio: 4990,
      moneda: "CLP",
      disponible: true,
      categorias: [{ id: "hogar", nombre: "Hogar" }],
    },
    {
      id: "prod_0003",
      nombre: "Botella térmica 500 ml",
      imagen_principal: {
        url: "/logo-todo-balato.png",
        texto_alternativo: "Botella térmica 500 ml",
      },
      precio: 5990,
      moneda: "CLP",
      disponible: true,
      categorias: [{ id: "accesorios", nombre: "Accesorios" }],
    },
    {
      id: "prod_0004",
      nombre: "Set de lápices gel x12",
      imagen_principal: {
        url: "/logo-todo-balato.png",
        texto_alternativo: "Set de lápices gel x12",
      },
      precio: 2490,
      moneda: "CLP",
      disponible: true,
      categorias: [{ id: "oficina", nombre: "Oficina" }],
    },
  ],
};

export const CONTENIDOS_INICIO_MOCK = {
  pagina: "inicio",
  results: [
    {
      pagina: "inicio",
      clave: "titulo",
      tipo: "texto",
      valor: "Bienvenido a Todo Balato",
      texto_alternativo: "",
    },
    {
      pagina: "inicio",
      clave: "eslogan",
      tipo: "texto",
      valor: "Bueno, bonito y balato.",
      texto_alternativo: "",
    },
    {
      pagina: "inicio",
      clave: "titulo_categorias",
      tipo: "texto",
      valor: "Categorías",
      texto_alternativo: "",
    },
    {
      pagina: "inicio",
      clave: "titulo_destacados",
      tipo: "texto",
      valor: "Productos destacados",
      texto_alternativo: "",
    },
    {
      pagina: "inicio",
      clave: "banner_principal",
      tipo: "imagen",
      valor: "/logo-todo-balato.png",
      texto_alternativo: "Ofertas destacadas de Todo Balato",
    },
    {
      pagina: "inicio",
      clave: "banner_enlace",
      tipo: "enlace",
      valor: "/catalogo",
      texto_alternativo: "",
    },
  ],
};

export const TEMAS_MOCK = {
  "balato-crema": {
    id: "balato-crema",
    nombre: "Balato crema",
    color_primario: "#BE1A19",
    color_secundario: "#800000",
    color_fondo: "#F9EBAC",
    color_texto: "#171717",
    color_acento: "#F7D87E",
    activo: true,
  },
  "balato-clasico": {
    id: "balato-clasico",
    nombre: "Balato clásico",
    color_primario: "#FF0000",
    color_secundario: "#000000",
    color_fondo: "#FFFFFF",
    color_texto: "#000000",
    color_acento: "#750000",
    activo: true,
  },
  "balato-oscuro": {
    id: "balato-oscuro",
    nombre: "Balato oscuro",
    color_primario: "#D0311E",
    color_secundario: "#800000",
    color_fondo: "#171717",
    color_texto: "#FFFFFF",
    color_acento: "#F7D87E",
    activo: true,
  },
  "balato-contraste": {
    id: "balato-contraste",
    nombre: "Balato contraste",
    color_primario: "#750000",
    color_secundario: "#000000",
    color_fondo: "#FFFFFF",
    color_texto: "#000000",
    color_acento: "#F7D87E",
    activo: true,
  },
};

export function obtenerModoMockInicio() {
  if (typeof window !== "undefined") {
    const parametro = new URLSearchParams(window.location.search).get("mockInicio");
    if (parametro) return parametro.trim().toLowerCase();
  }
  return (import.meta.env?.VITE_INICIO_MOCK || "").trim().toLowerCase();
}

export function usaMockCatalogo(modo) {
  return ["true", "1", "exito", "vacio", "error", "error_catalogo", "tema_oscuro", "tema_clasico"].includes(modo);
}

export function usaMockGestion(modo) {
  return [
    "true",
    "1",
    "exito",
    "gestion",
    "vacio",
    "error",
    "error_gestion",
    "tema_oscuro",
    "tema_clasico",
  ].includes(modo);
}
