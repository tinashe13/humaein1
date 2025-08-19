import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1', // Force IPv4
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Use IPv4 explicitly
        changeOrigin: true,
        secure: false,
      },
      '/metrics': {
        target: 'http://127.0.0.1:8000', // Use IPv4 explicitly
        changeOrigin: true,
        secure: false,
      },
    },
  },
})


