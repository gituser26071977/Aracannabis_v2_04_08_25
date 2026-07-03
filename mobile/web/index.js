/**
 * AraFlow — Web entry point.
 *
 * Mirrors `mobile/index.js` (native entry) but uses react-native-web's
 * AppRegistry instead of react-native's. The `App` component is the
 * same — only the runtime registration target differs.
 *
 * Web-only polyfills (Buffer / process / events) are loaded here so
 * they're guaranteed to be available before any RN module evaluates.
 */

import './polyfills';

import { AppRegistry } from 'react-native-web';

import { App } from '../src/App';
import { name as appName } from '../app.json';

AppRegistry.registerComponent(appName, () => App);

AppRegistry.runApplication(appName, {
  rootTag: document.getElementById('root'),
});
