import React from "react";
import { createRoot } from "react-dom/client";
import "maplibre-gl/dist/maplibre-gl.css";
import AutoRefreshingApp from "./AutoRefreshingApp";
import "./styles.css";
import "./accessibility.css";

const root = document.getElementById("root");
if (!root) throw new Error("root element is missing");

createRoot(root).render(
  <React.StrictMode>
    <AutoRefreshingApp />
  </React.StrictMode>,
);
