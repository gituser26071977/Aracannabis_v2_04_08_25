module.exports = {
  root: false,
  extends: ['../.eslintrc.cjs'],
  parserOptions: {
    project: ['./tsconfig.json'],
  },
  ignorePatterns: ['dist', 'node_modules'],
};
