import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // The API client (src/api/generated) fetches relative `/api/...` URLs, so in
    // development forward those to the FastAPI server (`uv run fastapi dev` in
    // ../server, port 8000). In production the API is expected to be served
    // same-origin under /api.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
