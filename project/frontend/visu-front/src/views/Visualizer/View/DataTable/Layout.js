import React from 'react';
import classnames from 'classnames';

export const Layout = ({ visible, children }) => (
  <div className={classnames({
    'data-table': true,
    'data-table--visible': visible,
  })}
  >
    {visible && children}
  </div>
);

export default Layout;
