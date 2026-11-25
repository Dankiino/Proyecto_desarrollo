// Aplica las variables CSS del tema activo.
const VARIABLES = {
  color_primario: "--tema-primario",
  color_secundario: "--tema-secundario",
  color_fondo: "--tema-fondo",
  color_texto: "--tema-texto",
  color_acento: "--tema-acento",
};

const HEX = /^#[0-9a-fA-F]{6}$/;

export function aplicarTema(tema) {
  const raiz = document.documentElement;
  if (!tema) return;
  for (const [campo, variable] of Object.entries(VARIABLES)) {
    if (HEX.test(tema[campo] || "")) raiz.style.setProperty(variable, tema[campo]);
  }
  raiz.dataset.tema = tema.id;
}
