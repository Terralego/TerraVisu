import WidgetSynthesis from './WidgetSynthesis';

import { connectView } from '../../context';

export default connectView(({ query, map, visibleBoundingBox, layersTreeState }) => ({
  query,
  map,
  visibleBoundingBox,
  displayedLayer: Array
    .from(layersTreeState)
    .filter(([, { table }]) => table)
    .map(([layer, state]) => ({ ...layer, state }))[0],
}))(WidgetSynthesis);
