import React from 'react';
import WidgetSynthesis from './WidgetSynthesis';
import { COMPONENT_SYNTHESIS } from './WidgetsTypes';
import WidgetLayout from './WidgetLayout';

const WidgetItem = ({
  widget,
  filters,
  layer,
  form,
  layerLabel,
  index,
  displayedLayers,
  translate,
  ...rest
}) => {
  const { component } = widget;

  if (component !== COMPONENT_SYNTHESIS) {
    return null;
  }

  const displayedLayer = displayedLayers.find(({ label }) => label === layerLabel);
  const title = translate('terralego.widget.synthesis.title', { layer: layerLabel });


  return (
    <WidgetLayout
      key={`${component}${index}`} // eslint-disable-line react/no-array-index-key
      widget={widget}
      title={title}
      {...rest}
    >
      <WidgetSynthesis
        {...widget}
        filters={filters}
        layer={layer}
        form={form}
        displayedLayer={displayedLayer}
      />
    </WidgetLayout>
  );
};

export default WidgetItem;
