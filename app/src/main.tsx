import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { ThemeProvider } from "./theme/theme-provider";
import { ErrorBoundary } from "./components/error-boundary";

const root = document.getElementById("root");
if (!root) {
  throw new Error("[HKI] Missing #root element in index.html");
}

createRoot(root).render(
  <StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
);
