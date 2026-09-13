import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/state": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080",
      "/ready": "http://127.0.0.1:8080",
      "/services": "http://127.0.0.1:8080",
      "/checks": "http://127.0.0.1:8080",
      "/auth": "http://127.0.0.1:8080",
      "/history": "http://127.0.0.1:8080",
      "/household": "http://127.0.0.1:8080",
      "/integrations": "http://127.0.0.1:8080"
    }
  }
});
