import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import vue from 'eslint-plugin-vue'
import globals from 'globals'
import { noDirectGlobals, noDirectGlobalsInTemplates } from '@mmit/ux-foundation/eslint'

const storageRestrictions = [{
  name: 'localStorage',
  message: 'Use safeStorage from @mmit/ux-foundation.',
}]

export default tseslint.config(
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  tseslint.configs.recommended,
  vue.configs['flat/essential'],
  {
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser, extraFileExtensions: ['.vue'] },
    },
  },
  {
    files: ['src/**/*.{js,mjs,cjs,ts,vue}'],
    rules: {
      ...noDirectGlobals(storageRestrictions),
      ...noDirectGlobalsInTemplates(storageRestrictions),
    },
  },
)
