import React from 'react';
import ReactDOM from 'react-dom';
import { Classes } from '@blueprintjs/core';

import ClusterList from './ClusterList';


export const generateClusterList = props => {
  const tooltipContainer = document.createElement('div');
  tooltipContainer.className = Classes.DARK;

  ReactDOM.render(
    <ClusterList
      {...props}
    />,
    tooltipContainer,
  );

  return tooltipContainer;
};

export default { generateClusterList };
