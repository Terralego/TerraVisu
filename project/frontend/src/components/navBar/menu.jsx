import React from 'react';
import './menu.css';
import PropTypes from 'prop-types';

function LoginButton(props) {
  const { loginUrl } = props;
  return (
    <a href={loginUrl}>Login</a>

  );
}
LoginButton.propTypes = {
  loginUrl: PropTypes.string.isRequired,
};

function LogoutButton(props) {
  return (
    <div>
      <span>{props.user.email}</span>
      <a href={props.instance.logoutUrl}>Logout</a>
    </div>
  );
}
export default function Menu(props) {
  if (props.user !== null) {
    return <LogoutButton user={props.user} instance={props.instance} />;
  }
  return <LoginButton loginUrl={props.instance.loginUrl} />;
}

Menu.propTypes = {
  instance: PropTypes.object.isRequired,
  user: PropTypes.object.isRequired,
};
