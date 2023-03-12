import React from 'react';

import context from './context';

const { Provider } = context;

export class MainProvider extends React.Component {
  state = {
    isHeaderOpen: false,
  };

  toggleHeader = state => this.setState(({ isHeaderOpen }) => ({
    isHeaderOpen: state === undefined
      ? !isHeaderOpen
      : state,
  }));

  render () {
    const { children } = this.props;
    const { isHeaderOpen } = this.state;
    const { toggleHeader } = this;
    const value = { isHeaderOpen, toggleHeader };
    return (
      <Provider value={value}>
        {children}
      </Provider>
    );
  }
}

export default MainProvider;
