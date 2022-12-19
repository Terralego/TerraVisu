import React from 'react';
import './navBar.css';
import { useQuery } from 'react-query';
import Menu from './menu';
import { fetchScenes } from '../../Api';

export default function Navbar(props) {
  const { user, instance } = props;
  const { isLoading, error, scenes } = useQuery('scenes', () => fetchScenes());
  return (
    <div className="heading">
      <img src={props.instance.logo} alt="logo" id="navbar-logo" />
      <h1>
        {props.instance.title}
        {' '}
        <Menu user={props.user} instance={props.instance} />
      </h1>
    </div>
  );
}
