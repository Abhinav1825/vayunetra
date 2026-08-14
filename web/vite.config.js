import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
<<<<<<< HEAD
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
                description: "The operations layer for urban air quality: source attribution, 72h forecasts, enforcement and citizen advisories.",
                start_url: "/",
                display: "standalone",
                background_color: "#1b294a",
                theme_color: "#1b294a",
                icons: [
                    { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
                    { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
                    { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
                ],
            },
        }),
    ],
=======
export default defineConfig({
    plugins: [react()],
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
    server: { port: 5173 },
});
