import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Proxy only for local dev (npm run dev)
    // Docker proxing /analyze, /history e.t.c. to backend
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/result':  'http://localhost:8000',
      '/health':  'http://localhost:8000',
    }
  }
})
