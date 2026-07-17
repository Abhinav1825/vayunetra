import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    // Real PWA: precache the app shell so it installs and boots offline
    // (the console's fixture mode then runs the full flow without a network).
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icon-192.png", "icon-512.png"],
      workbox: {
        // The console chunk (map libs) is large; raise the precache cap so the
        // shell is fully cached rather than silently skipped.
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        navigateFallback: "/index.html",
      },
      manifest: {
        name: "VayuNetra — Air Quality Intelligence",
        short_name: "VayuNetra",
        description:
          "The operations layer for urban air quality: source attribution, 72h forecasts, enforcement and citizen advisories.",
        start_url: "/",
        display: "standalone",
        background_color: "#0f172a",
        theme_color: "#0ea5e9",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
    }),
  ],
  server: { port: 5173 },
});
