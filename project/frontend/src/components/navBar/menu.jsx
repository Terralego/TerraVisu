import React from 'react';
import './menu.css';

function LoginButton(props) {
  const { loginUrl } = props;
  return (
    <a href={loginUrl}>Login</a>

  );
}

function LogoutButton({ instance, user }) {
  return (
    <div>
      <span>{user.email}</span>
      <a href={instance.logoutUrl}>Logout</a>
    </div>
  );
}
export default function Menu({ user, instance }) {
  if (user !== null) {
    return <LogoutButton user={user} instance={instance} />;
  }
  return <LoginButton loginUrl={instance.loginUrl} />;
}
