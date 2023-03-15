import React from 'react';
import { NavLink } from 'react-router-dom';

export const NotFound = () => (
  <p>
    Vue non trouvée. <NavLink to="/">Retour à l'accueil</NavLink>
  </p>
);

export default NotFound;
