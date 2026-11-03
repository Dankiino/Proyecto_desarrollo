import { useState } from "react";
import Card from "../components/Card";
import Button from "../components/Button";
import Field from "../components/Field";

export default function AuthPage({ sesion, onLogin, onRegistro, onLogout }) {
  const [esLogin, setEsLogin] = useState(true);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviar = async (evento) => {
    evento.preventDefault();
    setMensaje("");
    setError("");
    setCargando(true);

    try {
      if (esLogin) {
        await onLogin({ correo, password });
      } else {
        await onRegistro({ nombre, apellido, correo, password });
        setEsLogin(true);
        setPassword("");
        setMensaje("Cuenta creada. Ahora inicia sesión.");
      }
    } catch (solicitudError) {
      setError(solicitudError.message);
    } finally {
      setCargando(false);
    }
  };

  if (sesion) {
    return (
      <div className="pagina-angosta">
        <Card titulo="Mi cuenta">
          <p>Sesión iniciada: {sesion.usuario.nombre} {sesion.usuario.apellido}</p>
          <p>{sesion.usuario.correo}</p>
          {error && <p role="alert">{error}</p>}
          <Button label="Cerrar sesión" onClick={async () => {
            setError("");
            try {
              await onLogout();
            } catch (solicitudError) {
              setError(solicitudError.message);
            }
          }} />
        </Card>
      </div>
    );
  }

  return (
    <div className="pagina-angosta">
      <Card titulo={esLogin ? "Iniciar Sesión" : "Crear Cuenta"}>
        {mensaje && <p role="status">{mensaje}</p>}
        {error && <p role="alert">{error}</p>}
        <form onSubmit={enviar} className="auth-form">
          {!esLogin && (
            <>
              <Field id="nombre" label="Nombre" type="text" required value={nombre}
                onChange={(evento) => setNombre(evento.target.value)} />
              <Field id="apellido" label="Apellido" type="text" required value={apellido}
                onChange={(evento) => setApellido(evento.target.value)} />
            </>
          )}
          <Field id="correo" label="Correo Electrónico" type="email" required value={correo}
            onChange={(evento) => setCorreo(evento.target.value)} />
          <Field id="clave" label="Contraseña" type="password" required minLength={8}
            autoComplete={esLogin ? "current-password" : "new-password"} value={password}
            onChange={(evento) => setPassword(evento.target.value)} />
          <Button label={cargando ? "Enviando..." : esLogin ? "Ingresar" : "Registrarse"}
            type="submit" disabled={cargando} />
        </form>

        <div className="auth-toggle text-center">
          <button type="button" onClick={() => { setError(""); setMensaje(""); setEsLogin(!esLogin); }} className="btn-link">
            {esLogin ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
          </button>
        </div>
      </Card>
    </div>
  );
}
