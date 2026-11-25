import Button from "../components/Button";
import { campo, textoAlternativo } from "../services/contenidos";
import "./QuienesSomos.css";

export default function QuienesSomos({ contenidos, onNavegar }) {
  const titulo = campo(contenidos, "titulo", "¿Quiénes somos?");
  const textoPrincipal = campo(
    contenidos,
    "texto",
    "Somos Todo Balato, un mall chino con productos para el hogar, accesorios, artículos de uso diario y mucho más. Queremos ofrecerte una experiencia de compra cómoda, práctica y conveniente, con productos atractivos y precios accesibles."
  );
  const imagen = campo(contenidos, "imagen", "/logo-todo-balato.png");
  const imagenAlt = textoAlternativo(contenidos, "imagen", "Logo de Todo Balato");

  const valores = [
    [
      "01",
      "Variedad",
      "Productos para el hogar, accesorios, artículos de uso diario y mucho más.",
    ],
    [
      "02",
      "Precios accesibles",
      "Una propuesta para que comprar lo que necesitas no cueste una fortuna.",
    ],
    [
      "03",
      "Compra conveniente",
      "Queremos que tu experiencia sea cómoda, práctica y conveniente.",
    ],
  ];

  return (
    <div className="quienes-page">
      <section className="quienes-hero card" aria-labelledby="quienes-title">
        <div>
          <p className="quienes-etiqueta">CONÓCENOS</p>
          <h1 id="quienes-title">{titulo}</h1>
          <p>{textoPrincipal}</p>
        </div>
        <div className="quienes-logo-fondo">
          <img
            className="quienes-logo"
            src={imagen}
            alt={imagenAlt}
          />
        </div>
      </section>

      <section aria-labelledby="propuesta-title">
        <h2 id="propuesta-title" className="section-title text-center">
          Lo que nos representa
        </h2>
        <div className="quienes-valores">
          {valores.map(([numero, titulo, descripcion]) => (
            <article className="card quienes-valor" key={numero}>
              <span className="quienes-numero">{numero}</span>
              <h3>{titulo}</h3>
              <p>{descripcion}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="quienes-cierre" aria-label="Explorar la tienda">
        <div>
          <p>TODO BALATO</p>
          <h2>Bueno, bonito y balato.</h2>
        </div>
        <Button label="Ir al catálogo" onClick={() => onNavegar("catalogo")} />
      </section>
    </div>
  );
}
