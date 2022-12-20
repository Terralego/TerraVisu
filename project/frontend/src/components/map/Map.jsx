import React, { useRef, useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './Map.css';
import { MapboxStyleSwitcherControl } from 'mapbox-gl-style-switcher';
import 'mapbox-gl-style-switcher/styles.css';
import { useQuery } from 'react-query';
import fetchSettings from '../../Api';

export default function Map() {
  const { isLoading, data } = useQuery('settings', () => fetchSettings());
  const mapContainer = useRef(null);
  const map = useRef(null);
  const { lng, lat, zoom } = data.map.default;
  if (isLoading) {
    return <span>Loading...</span>;
  }
  useEffect(() => {
    if (map.current) return;
    const styles = [];

    data.map.baseLayers.forEach((element) => {
      styles.push({
        title: element.label,
        uri: element.url,
      });
    });
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      center: [lng, lat],
      zoom,
      style: styles[0].uri,
    });

    map.current.addControl(new MapboxStyleSwitcherControl(styles));
    map.current.addControl(new maplibregl.NavigationControl());
    map.current.addControl(new maplibregl.FullscreenControl());
    map.current.addControl(new maplibregl.ScaleControl());
  });

  return (
    <div className="map-wrap">
      <div ref={mapContainer} className="map" />
    </div>
  );
}
