import React from 'react';
import './navBar.css';
// import { useQuery } from 'react-query';
import Menu from './menu';
// import { fetchScenes } from '../../Api';

export default function Navbar({ user, instance }) {
  // const { isLoading, data } = useQuery('scenes', () => fetchScenes());
  return (
    <div className="heading">
      <img src={instance.logo} alt="logo" id="navbar-logo" />
      <h1>
        {instance.title}
        {' '}
        <Menu user={user} instance={instance} />
      </h1>
    </div>
  );
}
