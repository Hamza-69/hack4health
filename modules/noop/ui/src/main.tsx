import { ShellProvider } from "@h4h/module-ui";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ShellProvider>
      <App />
    </ShellProvider>
  </StrictMode>,
);
