import React from 'react';

export const AppName = ({ title = 'TerraVisu', version = 'v1.0' }) => (
  <div className="bp3-dark appName">
    <span className="appName-title">
      { title }
    </span>
    <span className="appName-version">{ version }</span>
  </div>
);


export default AppName;
