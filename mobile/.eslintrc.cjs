module.exports = {
  root: false,
  extends: ['../.eslintrc.cjs', '@react-native'],
  parserOptions: {
    project: ['./tsconfig.json'],
    tsconfigRootDir: __dirname,
  },
  ignorePatterns: [
    'node_modules',
    'android',
    'ios',
    'build',
    'coverage',
    'babel.config.js',
    'metro.config.js',
    'jest.config.js',
  ],
  rules: {
    'react-native/no-inline-styles': 'warn',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
};
