import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Fotos from "./pages/Fotos";
import Agendamentos from "./pages/Agendamentos";
import Historico from "./pages/Historico";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Navigate to="/fotos" replace />}
        />

        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/fotos"
          element={<Fotos />}
        />

        <Route
          path="/agendamentos"
          element={<Agendamentos />}
        />

        <Route
          path="/historico"
          element={<Historico />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;