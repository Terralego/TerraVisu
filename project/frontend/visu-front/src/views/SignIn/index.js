import React from 'react';
import { LoginForm, connectAuthProvider } from '@terralego/core/modules/Auth';

export const SignInView = ({ authenticated, logoutAction }) => (authenticated
  ? (
    <>
      <p>Vous êtes connecté !</p>
      <button type="button" onClick={logoutAction}>Déconnexion</button>
    </>
  )
  : <LoginForm />
);

export default connectAuthProvider('authenticated', 'logoutAction')(SignInView);
