import React, { useCallback } from 'react';
import { Icon } from '@blueprintjs/core';

const WidgetLayout = ({
  title,
  children,
  widget,
  layersTreeState,
  setLayerState,
}) => {
  const hideWidget = useCallback(() => {
    const [layer, state] = Array
      .from(layersTreeState)
      .find(([, { widgets = [] }]) => widgets.includes(widget));

    setLayerState({
      layer,
      state: {
        widgets: state.widgets.filter(w => w !== widget),
      },
    });
  }, [widget, layersTreeState, setLayerState]);

  return (
    <div className="widget">
      <div className="widget__header">
        <div className="widget__title">
          {title}
        </div>
        <div className="widget__buttons">
          <button
            type="button"
            onClick={hideWidget}
          >
            <Icon icon="cross" />
          </button>
        </div>
      </div>
      <div className="widget__body">
        {children}
      </div>
    </div>
  );
};

export default WidgetLayout;
