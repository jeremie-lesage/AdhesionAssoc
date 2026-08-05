import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config'

// La config de test réutilise celle de Vite (alias `@`, plugin Vue) pour éviter
// que les tests et le build divergent sur la résolution des imports.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./vitest.setup.ts'],
      include: ['src/**/*.spec.ts'],
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      coverage: {
        include: ['src/**/*.{ts,vue}'],
        exclude: ['src/main.ts', 'src/router/**', 'src/**/*.spec.ts'],
      },
    },
  }),
)
