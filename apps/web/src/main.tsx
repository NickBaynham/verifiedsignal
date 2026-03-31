import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { DemoDataProvider } from "./context/DemoDataContext";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <DemoDataProvider>
          <App />
        </DemoDataProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
