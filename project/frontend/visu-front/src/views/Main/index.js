import React from 'react';

import Header from './Header';
import Content from './Content';
import MainProvider from './Provider/MainProvider';
import Head from './Head';
import './styles.scss';
import SettingsProvider from './Provider/SettingsProvider';

export const Main = () => (
  <SettingsProvider>
    <MainProvider>
      <Head />
      <main className="main">
        <Header />
        <Content />
      </main>
    </MainProvider>
  </SettingsProvider>
);
export default Main;
