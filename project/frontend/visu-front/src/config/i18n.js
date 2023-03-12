import i18n from 'i18next';
import XHR from 'i18next-xhr-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import fr from '@terralego/core/locales/fr/translation';

const { PUBLIC_URL, REACT_APP_DEBUG } = process.env;

i18n
  .use(XHR)
  .use(LanguageDetector)
  .use(initReactI18next) // if not using I18nextProvider
  .init({
    backend: {
      loadPath: `${PUBLIC_URL}/locales/{{lng}}/{{ns}}.json`,
    },
    fallbackLng: 'fr',
    debug: !!REACT_APP_DEBUG,

    interpolation: {
      escapeValue: false, // not needed for react!!
    },

    // react i18next special options (optional)
    react: {
      wait: false,
      bindI18n: 'languageChanged loaded',
      bindStore: 'added removed',
      nsMode: 'default',
    },
  });

i18n.loadLanguages('fr')
  .then(() => i18n.addResourceBundle('fr', 'translation', fr, true));

export default i18n;
