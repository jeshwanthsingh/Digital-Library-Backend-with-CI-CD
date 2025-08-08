import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Proxy specific auth API requests to the backend
      '/api/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // No rewrite needed, backend expects /api/auth prefix
        // Ensure POST method is allowed (usually default, but explicit can help)
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'],
      },
      // Proxy other API requests to the backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // No rewrite needed, backend expects /api prefix
      },
      // Proxy static file requests to the backend
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // No rewrite needed, backend serves from /static
      }
    }
  }
});
