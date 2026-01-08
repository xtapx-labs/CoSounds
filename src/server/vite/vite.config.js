import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
    base: "/static/",
    server: {
        allowedHosts: ['10.0.0.57', 'localhost', '127.0.0.1', '0.0.0.0'],
        host: '0.0.0.0', // Listen on all addresses
        port: 5173,
        cors: true,      // Allow the phone to request resources
        hmr: {
            host: '10.0.0.57', // <--- IMPORTANT: Force the HMR connection to your IP
        },
    },
    build: {
        manifest: "manifest.json",
        outDir: resolve("./static"),
        assetsDir: "vite",
        rollupOptions: {
            input: {
                test: resolve("./assets/js/main.js"),
            },
            onwarn: (warning, warn) => (warning.code !== 'EVAL') ? warn(warning) : undefined // suppress eval warnings (@vue/devtools)

        }
    },
    plugins: [
        tailwindcss(),
    ]
})