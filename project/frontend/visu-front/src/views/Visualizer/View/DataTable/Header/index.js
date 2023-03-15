import Header from './Header';
import { connectView } from '../../context';

export default connectView(({ setLayerState, layersTreeState }) => ({
  setLayerState,
  displayedLayer: Array
    .from(layersTreeState)
    .find(([, { table }]) => table),
}))(Header);
