/**
 * AraFlow — Mobile entry point
 *
 * Este arquivo é o entrypoint registrado nas plataformas nativas
 * (iOS AppDelegate, Android MainApplication). A inicialização do app
 * (App.tsx) deve ocorrer DENTRO deste entry para garantir que polyfills
 * e side effects sejam executados antes do React.
 */

import { AppRegistry } from 'react-native';

import { App } from './src/App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
