import React from 'react';
import classnames from 'classnames';
import WidgetItem  from './WigetItem';
import './styles.scss';


const Widgets = ({
  widgets,
  visible,
  translate,
  layersTreeState,
  ...rest
}) => {
  const displayedLayers = React.useMemo(() =>
    (Array.from(layersTreeState, ([k1, k2]) => ({ ...k1, ...k2 }))
      .filter(({ active }) => active) || []),
  [layersTreeState]);

  if (!widgets.length) {
    return null;
  }

  return (
    <div
      className={classnames({
        'widgets-panel': true,
        'widgets-panel--visible': visible,
      })}
    >
      <div className="widgets-panel__container">
        {
          (widgets).map(({ widget, filters, layer, form, layerLabel }, index) => (
            <WidgetItem
              widget={widget}
              filters={filters}
              layer={layer}
              form={form}
              layerLabel={layerLabel}
              index={index}
              displayedLayers={displayedLayers}
              translate={translate}
              layersTreeState={layersTreeState}
              {...rest}
            />
          ))
        }
      </div>
    </div>
  );
};

export default Widgets;
