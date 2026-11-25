"""Datos iniciales de Gestión. Editar aquí y volver a cargar solo agrega lo que falta."""

TEMA_ACTIVO_POR_DEFECTO = "balato-clasico"

# id, nombre, primario, secundario, fondo, texto, acento
TEMAS = [
    ("balato-clasico", "Balato clásico", "#FF0000", "#000000", "#FFFFFF", "#000000", "#750000"),
    ("balato-crema", "Balato crema", "#BE1A19", "#800000", "#F9EBAC", "#171717", "#F7D87E"),
    ("balato-oscuro", "Balato oscuro", "#D0311E", "#800000", "#171717", "#FFFFFF", "#F7D87E"),
    ("balato-contraste", "Balato contraste", "#750000", "#000000", "#FFFFFF", "#000000", "#F7D87E"),
]

# pagina, clave, tipo, valor, texto_alternativo
CONTENIDOS = [
    ("inicio", "titulo", "texto", "Bienvenido a Todo Balato", ""),
    ("inicio", "eslogan", "texto", "Bueno, bonito y balato.", ""),
    ("inicio", "titulo_categorias", "texto", "Categorías", ""),
    ("inicio", "titulo_destacados", "texto", "Productos destacados", ""),
    ("inicio", "banner_principal", "imagen", "/logo-todo-balato.png", "Logo de Todo Balato"),
    ("inicio", "banner_enlace", "enlace", "/catalogo", ""),
    ("contacto", "titulo", "texto", "Contáctanos", ""),
    ("contacto", "introduccion", "texto", "¿Tienes dudas o comentarios? Escríbenos y te responderemos a la brevedad.", ""),
    ("contacto", "correo", "texto", "contacto@todobalato.example", ""),
    ("contacto", "telefono", "texto", "+56 2 2890 4310", ""),
    ("contacto", "horario", "texto", "Lunes a Viernes de 09:00 a 18:30 hrs · Sábados de 10:00 a 14:00 hrs", ""),
    ("quienes-somos", "titulo", "texto", "¿Quiénes somos?", ""),
    (
        "quienes-somos",
        "texto",
        "texto",
        "En Todo Balato somos un mall chino dedicado a ofrecer una gran variedad de productos "
        "para el hogar, accesorios, artículos de uso diario y mucho más, a precios accesibles "
        "para todos. Nuestro propósito es entregar una experiencia de compra cómoda, práctica y "
        "conveniente, combinando variedad, buenos precios y productos atractivos. Nos caracteriza "
        "nuestro compromiso con los clientes y nuestra filosofía: «Bueno, bonito y balato», porque "
        "creemos que comprar lo que necesitas no tiene por qué costar una fortuna.",
        "",
    ),
    ("quienes-somos", "imagen", "imagen", "/logo-todo-balato.png", "Logo de Todo Balato"),
]
