/**
 * mobile/web — ESLint configuration for the AraFlow RNW bundle.
 *
 * Rationale (RC1.2 / Option 3):
 *   - The top-level mobile/.eslintrc.cjs extends '@react-native', which
 *     uses @babel/eslint-parser and pulls react/jest/react-native plugins
 *     geared at the bare RN target.
 *   - mobile/web/** is the React Native Web bundle: webpack configs,
 *     polyfills, AsyncStorage shim, gesture-handler shim. The RN
 *     config conflicts with this layout (parser mismatch on
 *     consistent-type-imports; jest rules irrelevant on the bundle).
 *   - This config scopes lint to web/ explicitly with a minimal,
 *     self-contained ruleset. It does NOT extend the broken RN config.
 */

module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
  ],
  settings: {
    'import/resolver': {
      typescript: { project: './tsconfig.web.json' },
      node: true,
    },
  },
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    '@typescript-eslint/consistent-type-imports': 'error',
    'import/no-default-export': 'error',
    'import/order': [
      'error',
      {
        groups: [
          'builtin',
          'external',
          'internal',
          ['parent', 'sibling', 'index'],
        ],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true },
      },
    ],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'no-var': 'error',
    'prefer-const': 'error',
    'eqeqeq': ['error', 'always'],
  },
  ignorePatterns: [
    'dist/**',
    'node_modules/**',
  ],
  overrides: [
    {
      // Webpack configs and entry JS — plain ES modules. Disable the
      // type-aware TS rules (they need parserServices from
      // @typescript-eslint/parser which is not used on .js) and the
      // import-order rule (require() calls don't have a meaningful
      // group; alphabetizing them adds no value).
      files: ['*.js', '*.config.js'],
      parser: 'espree',
      rules: {
        '@typescript-eslint/no-var-requires': 'off',
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-unused-vars': 'off',
        '@typescript-eslint/consistent-type-imports': 'off',
        'import/order': 'off',
      },
    },
    {
      // TSX (shims may use JSX). Keep TS rules.
      files: ['*.tsx'],
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    {
      // Shim files mirror native module API contracts. They MUST
      // provide a default export (consumed via webpack alias, e.g.
      // `@react-native-async-storage/async-storage$` resolves to
      // shims/async-storage.web.ts whose default export replaces the
      // native `module.exports = AsyncStorage`). Removing the default
      // would break the alias. Same for `React.createElement` in the
      // gesture-handler shim — React's documented factory.
      files: ['shims/**/*.{ts,tsx}'],
      rules: {
        'import/no-default-export': 'off',
        'import/no-named-as-default-member': 'off',
      },
    },
  ],
};
