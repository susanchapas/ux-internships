import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // GitHub Pages project sites are served beneath the repository name.
  // The workflow supplies this value; local development keeps root-relative URLs.
  base: process.env.VITE_BASE_PATH ?? '/',
  plugins: [react()],
  server: {
    // Keep the Python backend unchanged while allowing the Vite client to use
    // the same relative /api URLs as the production server.
    proxy: {
      '/api': 'http://127.0.0.1:8080',
    },
  },
})
