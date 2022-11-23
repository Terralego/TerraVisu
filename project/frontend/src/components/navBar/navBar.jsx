import React from 'react';
import './navBar.css';
import Menu from './menu';

export default function Navbar() {
  const settings = JSON.parse(localStorage.getItem('settings'));
  return (
    <div className="heading">
      <img src={settings.instance.logo} alt="logo" id="navbar-logo" />
      <h1>
        {settings.instance.title}
        {' '}
        <Menu />
      </h1>
    </div>
  );
}
