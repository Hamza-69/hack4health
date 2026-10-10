import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { AuthProvider, RequireAuth } from "./auth";
import "./index.css";
import Layout from "./Layout";
import Login from "./pages/Login";
import ModulePage from "./pages/ModulePage";
import Tickets from "./pages/Tickets";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/tickets" replace />} />
            <Route path="/tickets" element={<Tickets />} />
            <Route path="/m/:name" element={<ModulePage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
