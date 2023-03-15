import { connectMain, connectSettings } from '../Provider/context';
import withEnv from '../../../config/withEnv';

import Header from './Header';

export default withEnv(connectMain('isHeaderOpen', 'toggleHeader')(connectSettings('settings')(Header)));
