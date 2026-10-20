import { useState } from "react";
import Card from "../components/Card";
import Button from "../components/Button";

const AuthPage = () => {
  const [esLogin, setEsLogin] = useState(true);

  return (
    <div style={{ maxWidth: "450px", margin: "0 auto" }}>
      <Card titulo={esLogin ? "Iniciar Sesión" : "Crear Cuenta"}>
        <form onSubmit={(e) => e.preventDefault()} className="auth-form">
          {!esLogin && (
            <div className="form-group">
              <label>Nombre Completo</label>
              <input type="text" placeholder="Ej: Juan Pérez" className="task-input" />
            </div>
          )}

          <div className="form-group">
            <label>Correo Electrónico</label>
            <input type="email" placeholder="correo@ejemplo.com" className="task-input" />
          </div>

          <div className="form-group">
            <label>Contraseña</label>
            <input type="password" placeholder="••••••••" className="task-input" />
          </div>

          <Button 
            label={esLogin ? "Ingresar" : "Registrarse"} 
            variant="primary" 
            type="submit"
          />
        </form>

        <div className="auth-toggle text-center">
          <button 
            onClick={() => setEsLogin(!esLogin)} 
            className="btn-link"
          >
            {esLogin ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
          </button>
        </div>
      </Card>
    </div>
  );
};

export default AuthPage;