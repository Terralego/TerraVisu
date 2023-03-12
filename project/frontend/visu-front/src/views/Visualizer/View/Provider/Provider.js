import React from 'react';

import context from '../context';

const { Provider } = context;

export class ViewProvider extends React.Component {
  state = {
    layersTreeState: new Map(),
  };

  componentWillUnmount () {
    this.isUnmount = true;
  }

  setMap = map => !this.isUnmount && this.setState({ map });

  setMapState = mapState => {
    const { onViewStateUpdate } = this.props;
    onViewStateUpdate({ map: mapState });
  };

  setLayersTreeState = layersTreeState =>
    !this.isUnmount && this.setState({ layersTreeState });

  setLayerState = ({ layer, state }) => {
    const { layersTreeState: prevLayersTreeState } = this.state;
    const layersTreeState = new Map(prevLayersTreeState);
    const newState = { ...layersTreeState.get(layer), ...state };
    layersTreeState.set(layer, newState);
    this.setLayersTreeState(layersTreeState);
  };

  searchQuery = query => {
    const { onViewStateUpdate } = this.props;
    onViewStateUpdate({ query });
  };

  setVisibleBoundingBox = bbox => !this.isUnmount && this.setState({ bbox });

  render () {
    const {
      children,
      view: {
        state: {
          query,
          map: mapState,
        } = {},
      },
    } = this.props;
    const { map, mapIsResizing, bbox, layersTreeState } = this.state;
    const {
      setLayersTreeState,
      setLayerState,
      setMap,
      setMapState,
      setVisibleBoundingBox,
      searchQuery,
    } = this;
    const value = {
      layersTreeState,
      setLayersTreeState,
      setLayerState,
      query,
      map,
      mapState,
      setMap,
      setMapState,
      mapIsResizing,
      searchQuery,
      setVisibleBoundingBox,
      visibleBoundingBox: bbox,
    };
    return (
      <Provider value={value}>
        {children}
      </Provider>
    );
  }
}

export default ViewProvider;
