import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/state": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080",
      "/services": "http://127.0.0.1:8080",
      "/check": "http://127.0.0.1:8080"
    }
  }
});
