import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: "@/lib", replacement: path.resolve(__dirname, "src/shared/lib") },
      { find: "@", replacement: path.resolve(__dirname, "src") },
    ],
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    proxy: {
      "/api": {
        target: process.env.VITE_PREVIEW_API_TARGET ?? "http://127.0.0.1:9001",
        changeOrigin: true,
      },
    },
  },
});
