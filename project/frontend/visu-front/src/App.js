import React, { Suspense } from 'react';
import { BrowserRouter } from 'react-router-dom';
import AuthProvider from '@terralego/core/modules/Auth';
import { ApiProvider } from '@terralego/core/modules/Api';
import StateProvider from '@terralego/core/modules/State/Hash';
import 'normalize.css/normalize.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/core/lib/css/blueprint.css';
import './app.scss';
import '@blueprintjs/datetime/lib/css/blueprint-datetime.css';

import SettingsProvider from './views/Main/Provider';
import withEnv from './config/withEnv';
import './config/i18n';
import Main from './views/Main';

// Used while loading translations. Don't want to display anything
const Loading = () => null;

const App = ({ env: { API_HOST } }) => (
  <ApiProvider host={API_HOST}>
    <AuthProvider>
      <StateProvider>
        <BrowserRouter>
          <Suspense fallback={<Loading />}>
            <SettingsProvider>
              <Main />
            </SettingsProvider>
          </Suspense>
        </BrowserRouter>
      </StateProvider>
    </AuthProvider>
  </ApiProvider>
);

export default withEnv(App);
