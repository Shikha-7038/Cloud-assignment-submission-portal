import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /api calls to the Flask backend during local development so the
// browser never needs to know the backend's port/host directly.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
