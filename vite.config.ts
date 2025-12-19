import path from 'path';
import os from 'os';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {

      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      optimizeDeps: {
        force: false, // Set to true to force re-optimization when needed
        include: ['react', 'react-dom', 'lucide-react', 'axios', 'recharts']
      },
      cacheDir: path.resolve(process.env.HOME || os.homedir(), '.vite-cache-healthpulse') // Use a cache directory in user's home directory
    };
});
