
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

import App from "./App.jsx";
import AdminPage from "./pages/AdminPage.jsx";

const esAdmin = window.location.pathname === "/admin";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    {esAdmin ? <AdminPage /> : <App />}
  </StrictMode>
);
