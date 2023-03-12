import React, { useState, useEffect } from 'react';

import { contextSettings } from './context';

const { Provider } = contextSettings;

const SETTINGS_PATH = '/settings.json';

const DEFAULT_SETTINGS = {
  favicon: '/terravisu/favicon.png',
  title: 'TerraVisu',
  version: 'v0.1',
  credits: 'Source: Terravisu',
  theme: {
    logo: '/images/terravisu-logo.png',
    brandLogo: '/images/terravisu-logo.png',
    logoUrl: '/',
    styles: [],
  },
  extraMenuItems: [],
  allowUserRegistration: false,
};


const getSettings =  async () => {
  try {
    const customSettings = await fetch(SETTINGS_PATH);
    return await customSettings.json();
  } catch (e) {
    try {
      const customSettings = await fetch('/api/settings/frontend');
      if (!customSettings.ok) {
        throw new Error('Unable to get response from API.');
      }
      return await customSettings.json();
    }
    catch (exc) {
      console.log('settings.json is missing. Please create a public/settings.json from public/settings.dist.json');
      return DEFAULT_SETTINGS;
    }
  }
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({});


  useEffect(() => {
    let isMounted = true;

    const loadSettings = async () => {
      const nextSettings = await getSettings();
      if (!isMounted) return;
      setSettings(nextSettings);
    };

    loadSettings();

    return () => { isMounted = false; };
  }, [setSettings]);

  const value = { settings };

  return (
    <Provider value={value}>
      {children}
    </Provider>
  );
};

export default SettingsProvider;
