import Widgets from './Widgets';
import { connectView } from '../context';

export default connectView(({ layersTreeState, setLayerState }) => {
  const widgets = Array
    .from(layersTreeState)
    .reduce((prev, [
      { filters: { layer, form } = {}, label },
      { widgets: layerWidgets = [], filters = {} },
    ]) => [
      ...prev,
      ...(layerWidgets
        .map(layerWidget => ({
          widget: layerWidget,
          filters,
          form,
          layer,
          layerLabel: label,
        }))
      ),
    ], []);
  return {
    visible: !!widgets.length,
    widgets,
    setLayerState,
    layersTreeState,
  };
})(Widgets);
