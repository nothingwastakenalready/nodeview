import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@fontsource/space-mono/400.css";
import "@fontsource/space-mono/700.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/space-grotesk/400.css";
import "@fontsource/space-grotesk/500.css";

import { App } from "./App";
import "./styles.css";
import "./visual-overrides.css";

const root = document.getElementById("root");
if (!root) throw new Error("missing root element");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);
