/**
 * AraFlow — Metro configuration
 * Configuração do bundler para React Native com suporte a monorepo
 * (acesso ao shared-contracts).
 */

const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

const path = require('path');

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '..');

const config = {
  watchFolders: [path.resolve(workspaceRoot, 'shared-contracts')],
  resolver: {
    nodeModulesPaths: [
      path.resolve(projectRoot, 'node_modules'),
      path.resolve(workspaceRoot, 'node_modules'),
    ],
    disableHierarchicalLookup: true,
  },
};

module.exports = mergeConfig(getDefaultConfig(projectRoot), config);
