import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginVitest from '@vitest/eslint-plugin'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,

  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/*.spec.ts'],
  },

  {
    name: 'app/rules',
    rules: {
      // Dette existante : les handlers d'erreur axios sont typés `any`. En
      // avertissement pour rendre la dette visible sans bloquer `npm run lint`.
      '@typescript-eslint/no-explicit-any': 'warn',
      // `const { adhesion_selected, ...rest } = formData` est la façon idiomatique
      // d'exclure un champ d'un objet : la variable extraite n'a pas à être lue.
      '@typescript-eslint/no-unused-vars': ['error', { ignoreRestSiblings: true }],
    },
  },

  // `skipFormatting` désactive les règles de mise en forme : c'est prettier qui
  // tranche, eslint ne s'occupe que de la correction.
  skipFormatting,
)
