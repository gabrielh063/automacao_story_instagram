import { NavLink } from "react-router-dom";

export default function Layout({ children }) {
  return (
    <div className="min-vh-100 bg-light">
      <nav className="navbar navbar-expand-lg bg-white border-bottom">
        <div className="container-fluid px-4">
          <span className="navbar-brand fw-bold">
            <i className="bi bi-instagram me-2"></i>
            Postagens Diárias
          </span>

          <div className="navbar-nav ms-auto gap-2">
            <NavLink
              to="/fotos"
              className={({ isActive }) =>
                `nav-link ${isActive ? "active fw-semibold" : ""}`
              }
            >
              Fotos
            </NavLink>

            <NavLink
              to="/agendamentos"
              className={({ isActive }) =>
                `nav-link ${isActive ? "active fw-semibold" : ""}`
              }
            >
              Agendamentos
            </NavLink>

            <NavLink
              to="/historico"
              className={({ isActive }) =>
                `nav-link ${isActive ? "active fw-semibold" : ""}`
              }
            >
              Histórico
            </NavLink>
          </div>
        </div>
      </nav>

      <main className="container py-4">
        {children}
      </main>
    </div>
  );
}