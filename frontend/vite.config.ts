import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // jsPDF optionally dynamic-imports canvg for SVG→Canvas conversion.
      // We never use that path (html2canvas rasterizes first), so point the
      // import at an empty stub to satisfy both esbuild and Vite's import analysis.
      canvg: path.resolve(__dirname, "src/stubs/canvg.ts"),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    hmr: {
      port: 5173,
    },
  },
});
