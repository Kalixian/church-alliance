import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['newton.jpoley.com'],
    // Set by docker-compose.dev.yml: file events don't cross bind mounts.
    watch: process.env.WATCH_POLLING ? { usePolling: true, interval: 300 } : undefined,
  },
})
