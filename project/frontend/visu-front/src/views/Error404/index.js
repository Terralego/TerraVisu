import React from 'react';
import { Link } from 'react-router-dom';
import { H1 } from '@blueprintjs/core';

const Error404View = () => (
  <div>
    <H1>Erreur 404 : Page introuvable.</H1>
    <p><strong>Retourner à la page d&#39;accueil: </strong>
      <Link to="/">Accueil</Link>
    </p>
  </div>
);

export default Error404View;
