import React from 'react';
import './navBar.css';

export default function Navbar() {
  const settings = JSON.parse(localStorage.getItem('settings'));
  return (
    <div className="heading">
      <h1>{settings.instance.title}</h1>
      <a href={settings.instance.loginUrl}>Login</a>
    </div>
  );
}
