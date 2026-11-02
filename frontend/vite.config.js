import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// En développement hors Docker, les appels /api sont redirigés vers un frontend déjà lancé
// par Docker Compose (npm run dev).
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: { '/api': 'http://localhost:8080' },
  },
})
