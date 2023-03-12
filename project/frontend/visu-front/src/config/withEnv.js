import React from 'react';

import { getEnv } from '../services/env';

export const withEnv = WrappedComponent =>
  class WithEnv extends React.Component {
    state = {};

    componentDidMount () {
      this.loadEnv();
    }

    async loadEnv () {
      try {
        const env = await getEnv();
        this.setState({ env });
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('env.json is invalid. Please create a public/env.json from public/env.dist.json');
      }
    }

    render () {
      const { env } = this.state;

      if (!env) return null;
      return <WrappedComponent env={env} {...this.props} />;
    }
  };

export default withEnv;
