import { useEffect, useState } from "react";
import {
    autenticarAdmin,
    listarProductosAdmin,
    crearProductoAdmin,
    editarProductoAdmin,
    desactivarProductoAdmin,
    listarCategoriasAdmin,
    crearCategoriaAdmin,
    editarCategoriaAdmin,
    listarMensajesContacto,
    obtenerMensajeContacto,
} from "../services/adminApi";

const productoVacio = {
    nombre: "",
    descripcion: "",
    precio: "",
    stock_fisico: "",
    categoria_id: "",
    imagenes: [
        { url: "", alt: "" },
        { url: "", alt: "" },
        { url: "", alt: "" },
        { url: "", alt: "" },
    ],
};

const categoriaVacia = {
    identificador: "",
    nombre: "",
    orden: "0",
};

export default function AdminPage() {
    const [correo, setCorreo] = useState("");
    const [password, setPassword] = useState("");
    const [sesion, setSesion] = useState(null);
    const [tipo, setTipo] = useState("productos");
    const [productos, setProductos] = useState([]);
    const [categorias, setCategorias] = useState([]);
    const [producto, setProducto] = useState(productoVacio);
    const [categoria, setCategoria] = useState(categoriaVacia);
    const [editando, setEditando] = useState(null);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");
    const [cargando, setCargando] = useState(false);
    const [mensajesContacto, setMensajesContacto] = useState([]);
    const [mensajeSeleccionado, setMensajeSeleccionado] = useState(null);
    const [cargandoContacto, setCargandoContacto] = useState(false);
    const [errorContacto, setErrorContacto] = useState("");


    const token = sesion?.tokens.access;

    const cargarMensajesContacto = async (accessToken) => {
        setCargandoContacto(true);
        setErrorContacto("");
        setMensajeSeleccionado(null);
        setMensajesContacto([]);

        try {
            const datos = await listarMensajesContacto(accessToken);
            setMensajesContacto(datos);
        } catch (e) {
            setErrorContacto(e.message);
        } finally {
            setCargandoContacto(false);
        }
    };

    const verMensajeContacto = async (id) => {
        setCargandoContacto(true);
        setErrorContacto("");
        setMensajeSeleccionado(null);

        try {
            const datos = await obtenerMensajeContacto(token, id);
            setMensajeSeleccionado(datos);
        } catch (e) {
            setErrorContacto(e.message);
        } finally {
            setCargandoContacto(false);
        }
    };

    const limpiarAvisos = () => {
        setError("");
        setMensaje("");
    };

    const cargarDatos = async (accessToken) => {
        const [respuestaProductos, respuestaCategorias] =
            await Promise.all([
                listarProductosAdmin(accessToken),
                listarCategoriasAdmin(accessToken),
            ]);

        setProductos(
            (respuestaProductos.productos || []).map((p) => ({
                ...p,
                identificador: p._id,
            }))
        );

        setCategorias(
            (respuestaCategorias.categorias || []).map((c) => ({
                ...c,
                identificador: c._id,
            }))
        );
    };

    const ingresar = async (e) => {
        e.preventDefault();
        limpiarAvisos();
        setCargando(true);

        try {
            const nuevaSesion = await autenticarAdmin(correo, password);

            // Comprobar también acceso real al Catálogo.
            await cargarDatos(nuevaSesion.tokens.access);

            setSesion(nuevaSesion);
            setPassword("");
            setMensaje("Acceso administrativo autorizado.");
        } catch (e) {
            setSesion(null);
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };


    const guardarProducto = async (e) => {
        e.preventDefault();
        limpiarAvisos();

        if (!producto.nombre.trim()) {
            setError("El nombre del producto es obligatorio.");
            return;
        }

        if (!producto.descripcion.trim()) {
            setError("La descripción es obligatoria.");
            return;
        }

        if (
            producto.precio === "" ||
            !Number.isInteger(Number(producto.precio)) ||
            Number(producto.precio) < 1
        ) {
            setError("El precio debe ser un entero mayor que cero.");
            return;
        }

        if (
            producto.stock_fisico === "" ||
            !Number.isInteger(Number(producto.stock_fisico)) ||
            Number(producto.stock_fisico) < 0
        ) {
            setError("El stock debe ser un entero no negativo.");
            return;
        }

        if (!producto.categoria_id) {
            setError("Debes seleccionar una categoría.");
            return;
        }

        if (
            producto.imagenes.length < 4 ||
            producto.imagenes.length > 6 ||
            producto.imagenes.some(
                (imagen) => !imagen.url.trim() || !imagen.alt.trim()
            )
        ) {
            setError("Debes ingresar entre 4 y 6 imágenes con URL y descripción.");
            return;
        }

        setCargando(true);

        try {
            const datos = {
                nombre: producto.nombre.trim(),
                descripcion: producto.descripcion.trim(),
                precio: Number(producto.precio),
                stock_fisico: Number(producto.stock_fisico),
                categoria_id: producto.categoria_id,
                imagenes: producto.imagenes.map((imagen) => ({
                    url: imagen.url.trim(),
                    alt: imagen.alt.trim(),
                })),
            };

            if (editando) {
                await editarProductoAdmin(token, editando, datos);
            } else {
                await crearProductoAdmin(token, datos);
            }

            await cargarDatos(token);
            setProducto(productoVacio);
            setEditando(null);
            setMensaje("Producto guardado correctamente en Catálogo.");
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };


    const guardarCategoria = async (e) => {
        e.preventDefault();
        limpiarAvisos();

        if (!categoria.nombre.trim()) {
            setError("El nombre de la categoría es obligatorio.");
            return;
        }

        if (!editando && !categoria.identificador.trim()) {
            setError("El identificador es obligatorio.");
            return;
        }

        if (!Number.isInteger(Number(categoria.orden))) {
            setError("El orden debe ser un número entero.");
            return;
        }

        setCargando(true);

        try {
            const datos = {
                nombre: categoria.nombre.trim(),
                orden: Number(categoria.orden),
            };

            if (editando) {
                await editarCategoriaAdmin(token, editando, datos);
            } else {
                await crearCategoriaAdmin(token, {
                    identificador: categoria.identificador.trim(),
                    ...datos,
                });
            }

            await cargarDatos(token);
            setCategoria(categoriaVacia);
            setEditando(null);
            setMensaje("Categoría guardada correctamente en Catálogo.");
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    const desactivar = async (id) => {
        if (!window.confirm(`¿Desactivar el producto ${id}?`)) return;

        limpiarAvisos();
        setCargando(true);

        try {
            await desactivarProductoAdmin(token, id);
            await cargarDatos(token);
            setMensaje("Producto desactivado correctamente.");
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    const reactivar = async (id) => {
        if (!window.confirm(`¿Activar nuevamente el producto ${id}?`)) return;

        limpiarAvisos();
        setCargando(true);

        try {
            await editarProductoAdmin(token, id, { activo: true });
            await cargarDatos(token);
            setMensaje("Producto activado correctamente.");
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };



    const iniciarEdicionProducto = (p) => {
        limpiarAvisos();

        setEditando(p.identificador);

        setProducto({
            nombre: p.nombre || "",
            descripcion: p.descripcion || "",
            precio: String(p.precio ?? ""),
            stock_fisico: String(p.stock_fisico ?? ""),
            categoria_id: p.categoria_id || "",
            imagenes: Array.isArray(p.imagenes)
                ? p.imagenes.map((imagen) => ({
                    url: imagen.url || "",
                    alt: imagen.alt || "",
                }))
                : [
                    { url: "", alt: "" },
                    { url: "", alt: "" },
                    { url: "", alt: "" },
                    { url: "", alt: "" },
                ],
        });
    };


    const iniciarEdicionCategoria = (c) => {
        limpiarAvisos();
        setEditando(c.identificador);
        setCategoria({
            identificador: c.identificador,
            nombre: c.nombre,
            orden: String(c.orden ?? 0),
        });
    };


    const cambiarSeccion = (seccion) => {
        limpiarAvisos();
        setTipo(seccion);
        setEditando(null);
        setProducto(productoVacio);
        setCategoria(categoriaVacia);

        if (seccion === "contacto") {
            cargarMensajesContacto(token);
        }
    };


    if (!sesion) {
        return (
            <section className="admin-login">
                <h1>Administración — Todo Balato</h1>
                <p>Ingresa con tu cuenta de administrador para gestionar productos y categorías.</p>

                <form onSubmit={ingresar} className="admin-form">
                    <label>
                        Correo administrativo
                        <input
                            type="email"
                            required
                            value={correo}
                            onChange={(e) => setCorreo(e.target.value)}
                            autoComplete="username"
                        />
                    </label>

                    <label>
                        Contraseña
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete="current-password"
                        />
                    </label>

                    <button disabled={cargando}>
                        {cargando ? "Validando..." : "Ingresar"}
                    </button>
                </form>

                {error && <p role="alert">{error}</p>}
            </section>
        );
    }

    return (
        <section className="admin-panel">
            <div className="admin-encabezado">
                <div>
                    <h1>Panel administrativo</h1>
                    <p>Cuenta: {sesion.usuario.correo}</p>
                </div>
                <button
                    type="button"
                    onClick={() => {
                        setSesion(null);
                        limpiarAvisos();
                    }}
                >
                    Salir del panel
                </button>
            </div>


            <div className="admin-pestanas">
                <button
                    type="button"
                    onClick={() => cambiarSeccion("productos")}
                    aria-pressed={tipo === "productos"}
                >
                    Productos
                </button>

                <button
                    type="button"
                    onClick={() => cambiarSeccion("categorias")}
                    aria-pressed={tipo === "categorias"}
                >
                    Categorías
                </button>

                <button
                    type="button"
                    onClick={() => cambiarSeccion("contacto")}
                    aria-pressed={tipo === "contacto"}
                >
                    Mensajes de contacto
                </button>
            </div>


            {mensaje && <p role="status" className="admin-exito">{mensaje}</p>}
            {error && <p role="alert" className="admin-error">{error}</p>}

            {tipo === "productos" ? (
                <>
                    <h2>{editando ? "Editar producto" : "Nuevo producto"}</h2>
                    <form className="admin-form" onSubmit={guardarProducto}>

                        <label>
                            Nombre
                            <input
                                required
                                maxLength={150}
                                value={producto.nombre}
                                onChange={(e) => setProducto({
                                    ...producto,
                                    nombre: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Descripción
                            <textarea
                                required
                                value={producto.descripcion}
                                onChange={(e) => setProducto({
                                    ...producto,
                                    descripcion: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Precio (CLP)
                            <input
                                type="number"
                                min="1"
                                step="1"
                                required
                                value={producto.precio}
                                onChange={(e) => setProducto({
                                    ...producto,
                                    precio: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Stock físico
                            <input
                                type="number"
                                min="0"
                                step="1"
                                required
                                value={producto.stock_fisico}
                                onChange={(e) => setProducto({
                                    ...producto,
                                    stock_fisico: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Categoría
                            <select
                                required
                                value={producto.categoria_id}
                                onChange={(e) => setProducto({
                                    ...producto,
                                    categoria_id: e.target.value,
                                })}
                            >
                                <option value="">Selecciona una categoría</option>
                                {categorias.filter((c) =>
                                    c.activa !== false ||
                                    c.identificador === producto.categoria_id
                                ).map((c) => (
                                    <option
                                        key={c.identificador}
                                        value={c.identificador}
                                    >
                                        {c.nombre}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <h3>Imágenes del producto</h3>
                        <p>Ingresa entre 4 y 6 imágenes.</p>

                        {producto.imagenes.map((imagen, indice) => (
                            <div key={indice} className="admin-imagen-campo">
                                <label>
                                    URL de imagen {indice + 1}
                                    <input
                                        type="url"
                                        required
                                        value={imagen.url}
                                        onChange={(e) => {
                                            const imagenes = producto.imagenes.map((item, i) =>
                                                i === indice
                                                    ? { ...item, url: e.target.value }
                                                    : item
                                            );
                                            setProducto({ ...producto, imagenes });
                                        }}
                                    />
                                </label>

                                <label>
                                    Descripción de imagen {indice + 1}
                                    <input
                                        required
                                        value={imagen.alt}
                                        onChange={(e) => {
                                            const imagenes = producto.imagenes.map((item, i) =>
                                                i === indice
                                                    ? { ...item, alt: e.target.value }
                                                    : item
                                            );
                                            setProducto({ ...producto, imagenes });
                                        }}
                                    />
                                </label>

                                {producto.imagenes.length > 4 && (
                                    <button
                                        type="button"
                                        onClick={() => setProducto({
                                            ...producto,
                                            imagenes: producto.imagenes.filter(
                                                (_, i) => i !== indice
                                            ),
                                        })}
                                    >
                                        Quitar imagen
                                    </button>
                                )}
                            </div>
                        ))}

                        {producto.imagenes.length < 6 && (
                            <button
                                type="button"
                                onClick={() => setProducto({
                                    ...producto,
                                    imagenes: [
                                        ...producto.imagenes,
                                        { url: "", alt: "" },
                                    ],
                                })}
                            >
                                + Agregar imagen
                            </button>
                        )}


                        <button disabled={cargando}>
                            {cargando ? "Guardando..." : "Guardar producto"}
                        </button>
                        {editando && (
                            <button type="button" onClick={() => {
                                setEditando(null);
                                setProducto(productoVacio);
                            }}>
                                Cancelar edición
                            </button>
                        )}
                    </form>

                    <div className="admin-seccion-titulo">
                        <div>
                            <h2>Inventario de productos</h2>
                            <p>Administra los productos disponibles en tu tienda.</p>
                        </div>
                        <span className="admin-contador">
                            {productos.length} productos
                        </span>
                    </div>

                    <div className="admin-resumen">
                        <article>
                            <span>Total productos</span>
                            <strong>{productos.length}</strong>
                        </article>
                        <article>
                            <span>Activos</span>
                            <strong>{productos.filter(p => p.activo).length}</strong>
                        </article>
                        <article>
                            <span>Inactivos</span>
                            <strong>{productos.filter(p => !p.activo).length}</strong>
                        </article>
                        <article>
                            <span>Sin stock</span>
                            <strong>
                                {productos.filter(p => p.stock_fisico <= 0).length}
                            </strong>
                        </article>
                    </div>

                    <div className="admin-listado">
                        {productos.map((p) => (
                            <article key={p.identificador} className="admin-registro">
                                <div className="admin-producto-datos">
                                    <strong>{p.nombre}</strong>
                                    <small>ID: {p.identificador}</small>
                                    <small>
                                        {p.descripcion || "Sin descripción"}
                                    </small>
                                </div>

                                <div className="admin-producto-stock">
                                    <span>Precio</span>
                                    <strong>
                                        {Number(p.precio).toLocaleString("es-CL", {
                                            style: "currency",
                                            currency: "CLP",
                                            maximumFractionDigits: 0,
                                        })}
                                    </strong>
                                </div>

                                <div className="admin-producto-stock">
                                    <span>Stock físico</span>
                                    <strong>{p.stock_fisico ?? 0} unidades</strong>
                                </div>

                                <div className="admin-producto-acciones">
                                    <span className={`admin-estado ${p.activo ? "activo" : "inactivo"}`}>
                                        {p.activo ? "Activo" : "Inactivo"}
                                    </span>

                                    <button
                                        type="button"
                                        className="admin-btn-editar"
                                        disabled={cargando}
                                        onClick={() => iniciarEdicionProducto(p)}
                                    >
                                        Editar
                                    </button>

                                    {p.activo ? (
                                        <button
                                            type="button"
                                            className="admin-btn-desactivar"
                                            disabled={cargando}
                                            onClick={() => desactivar(p.identificador)}
                                        >
                                            Desactivar
                                        </button>
                                    ) : (
                                        <button
                                            type="button"
                                            className="admin-btn-activar"
                                            disabled={cargando}
                                            onClick={() => reactivar(p.identificador)}
                                        >
                                            Activar
                                        </button>
                                    )}
                                </div>
                            </article>
                        ))}
                    </div>
                </>
            ) : tipo === "categorias" ? (
                <>
                    <h2>{editando ? "Editar categoría" : "Nueva categoría"}</h2>
                    <form className="admin-form" onSubmit={guardarCategoria}>
                        <label>
                            Identificador
                            <input
                                required
                                disabled={Boolean(editando)}
                                value={categoria.identificador}
                                onChange={(e) => setCategoria({
                                    ...categoria, identificador: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Nombre
                            <input
                                required
                                value={categoria.nombre}
                                onChange={(e) => setCategoria({
                                    ...categoria, nombre: e.target.value,
                                })}
                            />
                        </label>

                        <label>
                            Orden
                            <input
                                type="number"
                                step="1"
                                required
                                value={categoria.orden}
                                onChange={(e) => setCategoria({
                                    ...categoria, orden: e.target.value,
                                })}
                            />
                        </label>

                        <button disabled={cargando}>
                            {cargando ? "Guardando..." : "Guardar categoría"}
                        </button>

                        {editando && (
                            <button type="button" onClick={() => {
                                setEditando(null);
                                setCategoria(categoriaVacia);
                            }}>
                                Cancelar edición
                            </button>
                        )}
                    </form>

                    <h2>Categorías registradas</h2>
                    <div className="admin-listado">
                        {categorias.map((c) => (
                            <article key={c.identificador} className="admin-registro">
                                <strong>{c.nombre}</strong>
                                <span>Orden: {c.orden}</span>
                                <button onClick={() => iniciarEdicionCategoria(c)}>
                                    Editar
                                </button>
                            </article>
                        ))}
                    </div>

                </>
            ) : tipo === "contacto" ? (
                <div className="admin-contacto">
                    <div className="admin-contacto-encabezado">
                        <h2>Mensajes de contacto</h2>

                        <button
                            type="button"
                            disabled={cargandoContacto}
                            onClick={() => cargarMensajesContacto(token)}
                        >
                            Actualizar mensajes
                        </button>
                    </div>

                    {errorContacto && (
                        <p role="alert" className="admin-error">
                            {errorContacto}
                        </p>
                    )}

                    {cargandoContacto && (
                        <p role="status">Cargando mensajes...</p>
                    )}

                    {!cargandoContacto &&
                        !errorContacto &&
                        mensajesContacto.length === 0 && (
                            <p>No hay mensajes recibidos.</p>
                        )}

                    {!cargandoContacto &&
                        !errorContacto &&
                        mensajesContacto.length > 0 && (
                            <div className="admin-listado">
                                {mensajesContacto.map((item) => (
                                    <article
                                        key={item.id}
                                        className="admin-registro"
                                    >
                                        <strong>{item.nombre}</strong>
                                        <span>{item.correo}</span>
                                        <span>
                                            {new Date(
                                                item.fecha_recepcion
                                            ).toLocaleString("es-CL")}
                                        </span>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                verMensajeContacto(item.id)
                                            }
                                        >
                                            Ver mensaje
                                        </button>

{mensajeSeleccionado?.id === item.id && (
    <div className="admin-contacto-detalle">
        <div className="admin-contacto-detalle-cabecera">
            <h3>Detalle del mensaje</h3>
            <button
                type="button"
                onClick={() => setMensajeSeleccionado(null)}
            >
                Cerrar ✕
            </button>
        </div>

        <div className="admin-contacto-info">
            <p><strong>Nombre:</strong> {mensajeSeleccionado.nombre}</p>
            <p><strong>Correo:</strong> {mensajeSeleccionado.correo}</p>
            <p>
                <strong>Fecha:</strong>{" "}
                {new Date(
                    mensajeSeleccionado.fecha_recepcion
                ).toLocaleString("es-CL")}
            </p>
        </div>

        <div className="admin-contacto-mensaje">
            <strong>Mensaje recibido</strong>
            <p>{mensajeSeleccionado.mensaje}</p>
        </div>
    </div>
)}

                                    </article>
                                ))}
                            </div>
                        )}
                </div>
            ) : null}
        </section>
    );
}
