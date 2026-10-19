
export default function Footer() {
    return (
        <footer className="footer">
            <div className="footer-contenido">
                <div className="footer-marca">
                    <img
                        src="/logo-todo-balato.png"
                        alt="Logo Todo Balato"
                        className="footer-logo"
                    />
                    <h3>TODO BALATO</h3>
                    <p>Bueno, bonito y barato.</p>
                </div>

                <div className="footer-enlaces">
                    <h3>Navegación</h3>
                    <a href="/">Inicio</a>
                    <a href="/catalogo">Catálogo</a>
                    <a href="/nosotros">Nosotros</a>
                    <a href="/contacto">Contacto</a>
                </div>

                <div className="footer-enlaces">
                    <h3>Ayuda</h3>
                    <a href="/carrito">Mi carrito</a>
                    <a href="/contacto">Atención al cliente</a>
                </div>
            </div>

            <div className="footer-inferior">
                © {new Date().getFullYear()} Todo Balato.
                Todos los derechos reservados.
            </div>
        </footer>
    );
}
