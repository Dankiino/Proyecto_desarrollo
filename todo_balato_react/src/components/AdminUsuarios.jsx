import { useEffect, useRef, useState } from "react";
import {
    bloquearUsuarioAdmin,
    crearUsuarioAdmin,
    desbloquearUsuarioAdmin,
    editarUsuarioAdmin,
    importarUsuariosCSVAdmin,
    listarUsuariosAdmin,
} from "../services/adminApi";

const usuarioVacio = {
    nombre: "",
    apellido: "",
    correo: "",
    password: "",
    rol: "CLIENTE",
};

function descargarInforme(informe) {
    const filas = [
        ["resultado", "fila", "correo", "id", "razon"],
        ...informe.aceptados.map((fila) => [
            "aceptado", fila.fila, fila.correo, fila.id, "",
        ]),
        ...informe.rechazados.map((fila) => [
            "rechazado", fila.fila, fila.correo, "", fila.razon,
        ]),
    ];
    const contenido = filas
        .map((fila) => fila.map((valor) =>
            `"${String(valor ?? "").replaceAll('"', '""')}"`
        ).join(","))
        .join("\r\n");
    const url = URL.createObjectURL(
        new Blob(["\uFEFF", contenido], { type: "text/csv;charset=utf-8" })
    );
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "informe-importacion-usuarios.csv";
    enlace.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function AdminUsuarios({ token, usuarioActualId }) {
    const [usuarios, setUsuarios] = useState([]);
    const [formulario, setFormulario] = useState(usuarioVacio);
    const [editando, setEditando] = useState(null);
    const [archivo, setArchivo] = useState(null);
    const [informe, setInforme] = useState(null);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");
    const [cargando, setCargando] = useState(false);
    const inputCSV = useRef(null);

    const cargarUsuarios = async () => {
        setCargando(true);
        setError("");
        try {
            const respuesta = await listarUsuariosAdmin(token);
            setUsuarios(respuesta);
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        let vigente = true;
        listarUsuariosAdmin(token)
            .then((respuesta) => {
                if (vigente) setUsuarios(respuesta);
            })
            .catch((e) => {
                if (vigente) setError(e.message);
            });
        return () => {
            vigente = false;
        };
    }, [token]);

    const limpiarFormulario = () => {
        setFormulario(usuarioVacio);
        setEditando(null);
    };

    const guardarUsuario = async (e) => {
        e.preventDefault();
        setError("");
        setMensaje("");
        setCargando(true);
        const datos = {
            nombre: formulario.nombre.trim(),
            apellido: formulario.apellido.trim(),
            correo: formulario.correo.trim(),
            rol: formulario.rol,
        };
        if (formulario.password) datos.password = formulario.password;
        try {
            if (editando) {
                await editarUsuarioAdmin(token, editando, datos);
                setMensaje("Usuario actualizado.");
            } else {
                await crearUsuarioAdmin(token, { ...datos, password: formulario.password });
                setMensaje("Usuario creado como cuenta activa.");
            }
            limpiarFormulario();
            await cargarUsuarios();
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    const cambiarEstado = async (usuario) => {
        setError("");
        setMensaje("");
        setCargando(true);
        try {
            if (usuario.estado === "BLOQUEADO") {
                await desbloquearUsuarioAdmin(token, usuario.id);
                setMensaje("Usuario desbloqueado.");
            } else {
                await bloquearUsuarioAdmin(token, usuario.id);
                setMensaje("Usuario bloqueado.");
            }
            await cargarUsuarios();
        } catch (e) {
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    const importarCSV = async (e) => {
        e.preventDefault();
        setError("");
        setMensaje("");
        setInforme(null);
        if (!archivo) {
            setError("Selecciona un archivo CSV UTF-8.");
            return;
        }
        setCargando(true);
        try {
            const resultado = await importarUsuariosCSVAdmin(token, archivo);
            setInforme(resultado);
            setMensaje(`Importación terminada: ${resultado.aceptados.length} aceptados, ${resultado.rechazados.length} rechazados.`);
            setArchivo(null);
            if (inputCSV.current) inputCSV.current.value = "";
            await cargarUsuarios();
        } catch (e) {
            if (e.reporte) setInforme(e.reporte);
            setError(e.message);
        } finally {
            setCargando(false);
        }
    };

    return (
        <section className="admin-usuarios">
            <h2>Administrar usuarios</h2>
            {mensaje && <p role="status" className="admin-exito">{mensaje}</p>}
            {error && <p role="alert" className="admin-error">{error}</p>}

            <h3>{editando ? "Editar usuario" : "Crear usuario"}</h3>
            <form className="admin-form" onSubmit={guardarUsuario}>
                <label>
                    Nombre
                    <input required maxLength="100" value={formulario.nombre}
                        onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })} />
                </label>
                <label>
                    Apellido
                    <input required maxLength="100" value={formulario.apellido}
                        onChange={(e) => setFormulario({ ...formulario, apellido: e.target.value })} />
                </label>
                <label>
                    Correo
                    <input required type="email" value={formulario.correo}
                        onChange={(e) => setFormulario({ ...formulario, correo: e.target.value })} />
                </label>
                <label>
                    {editando ? "Nueva contraseña (opcional)" : "Contraseña inicial"}
                    <input type="password" autoComplete="new-password"
                        required={!editando} value={formulario.password}
                        onChange={(e) => setFormulario({ ...formulario, password: e.target.value })} />
                </label>
                <label>
                    Rol
                    <select value={formulario.rol}
                        onChange={(e) => setFormulario({ ...formulario, rol: e.target.value })}>
                        <option value="CLIENTE">CLIENTE</option>
                        <option value="ADMIN">ADMIN</option>
                    </select>
                </label>
                <button disabled={cargando}>{editando ? "Guardar cambios" : "Crear usuario"}</button>
                {editando && <button type="button" onClick={limpiarFormulario}>Cancelar</button>}
            </form>

            <h3>Importar usuarios desde CSV</h3>
            <p>
                UTF-8 con encabezados <code>nombre,apellido,correo,password</code>;
                <code> rol</code> es opcional y por defecto es CLIENTE. Cada fila
                válida se guarda aunque otras tengan errores. Las contraseñas no
                se incluyen en el informe.
            </p>
            <form className="admin-form" onSubmit={importarCSV}>
                <label>
                    Archivo CSV
                    <input ref={inputCSV} type="file" accept=".csv,text/csv" required
                        onChange={(e) => setArchivo(e.target.files?.[0] || null)} />
                </label>
                <button disabled={cargando || !archivo}>
                    {cargando ? "Procesando..." : "Importar CSV"}
                </button>
            </form>

            {informe && (
                <section aria-label="Informe de importación">
                    <h3>Informe de importación ({informe.total} filas)</h3>
                    <p>{informe.regla}</p>
                    <button type="button" onClick={() => descargarInforme(informe)}>
                        Descargar informe CSV
                    </button>
                    <h4>Aceptados ({informe.aceptados.length})</h4>
                    {informe.aceptados.map((fila) => (
                        <p key={`ok-${fila.fila}`}>Fila {fila.fila}: {fila.correo} — aceptada</p>
                    ))}
                    <h4>Rechazados ({informe.rechazados.length})</h4>
                    {informe.rechazados.map((fila, indice) => (
                        <p key={`error-${fila.fila}-${indice}`}>
                            Fila {fila.fila}: {fila.correo || "(sin correo)"} — {fila.razon}
                        </p>
                    ))}
                </section>
            )}

            <h3>Usuarios registrados</h3>
            {cargando && <p role="status">Cargando...</p>}
            <div className="admin-listado">
                {usuarios.map((usuario) => (
                    <article className="admin-registro" key={usuario.id}>
                        <strong>{usuario.nombre} {usuario.apellido}</strong>
                        <span>{usuario.correo}</span>
                        <span>{usuario.rol} · {usuario.estado}</span>
                        <button type="button" disabled={cargando} onClick={() => {
                            setError("");
                            setMensaje("");
                            setEditando(usuario.id);
                            setFormulario({
                                nombre: usuario.nombre,
                                apellido: usuario.apellido,
                                correo: usuario.correo,
                                password: "",
                                rol: usuario.rol,
                            });
                        }}>
                            Editar
                        </button>
                        <button type="button" disabled={cargando || usuario.id === usuarioActualId}
                            onClick={() => cambiarEstado(usuario)}>
                            {usuario.estado === "BLOQUEADO" ? "Desbloquear" : "Bloquear"}
                        </button>
                    </article>
                ))}
            </div>
        </section>
    );
}
