import React from 'react';
import './menu.css';

const settings = JSON.parse(localStorage.getItem('settings'));

function LoginButton() {
  return (
    <a href={settings.instance.loginUrl}>Login</a>
  );
}

function LogoutButton() {
  return (
    <div>
      <span>{settings.user.email}</span>
      <a href={settings.instance.logoutUrl}>Logout</a>
    </div>
  );
}
export default function Menu() {
  if (settings.user !== null) {
    return <LogoutButton />;
  }
  return <LoginButton />;
}
