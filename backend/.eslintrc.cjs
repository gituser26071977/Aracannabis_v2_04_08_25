module.exports = {
  root: false,
  extends: ['../../.eslintrc.cjs'],
  parserOptions: {
    project: ['./tsconfig.json'],
  },
  env: {
    node: true,
    jest: true,
  },
  ignorePatterns: ['dist', 'node_modules', 'coverage'],
};
