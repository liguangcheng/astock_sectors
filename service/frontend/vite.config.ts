import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 开发：前端 5173，/api 代理到后端 3999；生产：build 产物由后端 3999 直接托管
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3999',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1500,
  },
});
