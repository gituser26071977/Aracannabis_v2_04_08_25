/**
 * AraFlow — Babel configuration
 * Configura aliases de paths, preset React Native, e transformação de
 * TypeScript.
 */

module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./'],
        alias: {
          '@core': './src/core',
          '@features': './src/features',
          '@shared': './src/shared',
          '@infrastructure': './src/infrastructure',
          '@contracts': '../shared-contracts/src',
        },
        extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
      },
    ],
  ],
};
