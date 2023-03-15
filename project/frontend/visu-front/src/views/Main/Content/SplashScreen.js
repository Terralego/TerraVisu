import { useEffect } from 'react';

export const SplashScreen = ({ children }) => {
  useEffect(() => {
    document.body.classList.remove('with-splash');
    setTimeout(() => {
      const splashScreen = document.querySelector('.splash-screen_container');
      splashScreen && splashScreen.remove();
    }, 5000);
  }, []);
  return children;
};

export default SplashScreen;
