import React from 'react';
import { withRouter } from 'react-router-dom';

import SplashScreen from '../Main/Content/SplashScreen';
import Visualizer from './Visualizer';
import withEnv from '../../config/withEnv';

export default withRouter(withEnv(props => <SplashScreen><Visualizer {...props} /></SplashScreen>));
