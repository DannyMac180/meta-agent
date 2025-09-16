import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    testTimeout: 30000, // Allow time for Docker operations
    setupFiles: [],
    coverage: {
      reporter: ['text', 'html'],
      exclude: [
        'node_modules',
        'dist',
        'test',
        'docker'
      ]
    }
  }
});
