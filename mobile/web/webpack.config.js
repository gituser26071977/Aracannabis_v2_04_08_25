/**
 * AraFlow — Webpack 5 configuration (production + development basis).
 *
 * Architecture decisions (locked by plan approval):
 *
 *   1. `react-native$` is aliased to `react-native-web` so every import
 *      of `react-native` lands on the web implementation. This is the
 *      standard RNW webpack pattern.
 *
 *   2. `react-native-gesture-handler` is aliased to a thin `<div>` shim
 *      because the package is native-only and App.tsx imports
 *      `GestureHandlerRootView` (used as a root wrapper, no gestures).
 *
 *   3. `@react-native-async-storage/async-storage` is aliased to a
 *      localStorage-backed shim that mirrors the subset of the native
 *      API used by `features/session/Clinical/feedback/FeedbackStorage`.
 *
 *   4. Babel uses the project's existing `@react-native/babel-preset`
 *      + `babel-plugin-module-resolver` (same setup as Metro), so the
 *      `@core/*`, `@features/*`, etc. aliases resolve identically on
 *      web and native. No duplicated alias config.
 *
 *   5. Webpack reads TypeScript and JSX through Babel — tsc is NOT
 *      invoked. This keeps the build fast and avoids double-transpile.
 *      Type errors are caught by the separate `npm run typecheck`.
 *
 *   6. `dev` mode is selected by webpack's `--mode` flag. `npm run
 *      web:dev` adds the dev-server in `webpack.config.dev.js`.
 */

const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const projectRoot = path.resolve(__dirname, '..');

/** @returns {import('webpack').Configuration} */
module.exports = (env, argv) => {
  const isProd = argv.mode === 'production';

  return {
    mode: isProd ? 'production' : 'development',
    entry: path.resolve(__dirname, 'index.js'),
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: isProd ? 'assets/[name].[contenthash:8].js' : 'assets/[name].js',
      chunkFilename: isProd ? 'assets/[name].[contenthash:8].chunk.js' : 'assets/[name].chunk.js',
      assetModuleFilename: 'assets/[name].[hash:8][ext]',
      publicPath: '/',
      clean: true,
    },
    resolve: {
      alias: {
        // Core RN → RNW
        'react-native$': 'react-native-web',
        // Native-only modules → web shims
        'react-native-gesture-handler$': path.resolve(__dirname, 'shims/gesture-handler.web.tsx'),
        '@react-native-async-storage/async-storage$': path.resolve(
          __dirname,
          'shims/async-storage.web.ts',
        ),
        // Mirror babel module-resolver aliases so webpack + babel agree.
        '@core': path.resolve(projectRoot, 'src/core'),
        '@features': path.resolve(projectRoot, 'src/features'),
        '@shared': path.resolve(projectRoot, 'src/shared'),
        '@infrastructure': path.resolve(projectRoot, 'src/infrastructure'),
        '@contracts': path.resolve(projectRoot, '../shared-contracts/src'),
        '@araflow/shared-contracts': path.resolve(projectRoot, '../shared-contracts/src/index.ts'),
      },
      extensions: [
        '.web.tsx',
        '.web.ts',
        '.web.jsx',
        '.web.js',
        '.tsx',
        '.ts',
        '.jsx',
        '.js',
        '.json',
      ],
    },
    module: {
      rules: [
        {
          test: /\.(ts|tsx|js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              babelrc: false,
              configFile: path.resolve(projectRoot, 'babel.config.js'),
              cacheDirectory: true,
            },
          },
        },
        {
          test: /\.(png|jpe?g|gif|svg|webp|ico)$/i,
          type: 'asset/resource',
        },
        {
          test: /\.(woff2?|ttf|eot|otf)$/i,
          type: 'asset/resource',
        },
      ],
    },
    plugins: [
      // Injeta globals que Metro fornece nativamente mas webpack não:
      //   __DEV__  → true em development, false em production (modo webpack)
      // Sem isto, qualquer `if (__DEV__) ...` ou referência a __DEV__
      // quebra em runtime com "ReferenceError: __DEV__ is not defined".
      new webpack.DefinePlugin({
        __DEV__: JSON.stringify(!isProd),
        'process.env.NODE_ENV': JSON.stringify(isProd ? 'production' : 'development'),
      }),
      new HtmlWebpackPlugin({
        template: path.resolve(__dirname, 'index.html'),
        inject: 'body',
        minify: isProd,
      }),
    ],
    performance: {
      hints: isProd ? 'warning' : false,
      maxAssetSize: 600 * 1024,
      maxEntrypointSize: 600 * 1024,
    },
    devtool: isProd ? 'source-map' : 'eval-cheap-module-source-map',
    stats: 'minimal',
  };
};
