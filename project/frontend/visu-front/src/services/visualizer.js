import Api from '@terralego/core/modules/Api';
import { sortCustomLayers } from '@terralego/core/modules/Visualizer/services/layersTreeUtils';
import memoizee from 'memoizee';
import defaultIcon from '../images/defaultLogo.svg';

export const fetchViewConfig = memoizee(async viewName => {
  try {
    const config = await Api.request(`geolayer/view/${viewName}/`);

    // Replace '/api/' part in urls with the API_HOST value to be able to reach the
    // configured backend
    const configWithHost = JSON.parse(JSON.stringify(config).replace(/"\/api(\/[^"]+)"/g, `"${Api.host}$1"`));

    const { layersTree, map: { customStyle: { layers } = {} } = {} } = configWithHost;

    configWithHost.map = configWithHost.map || {};
    configWithHost.map.customStyle = configWithHost.map.customStyle || {};
    configWithHost.map.customStyle.layers = sortCustomLayers(layers, layersTree);

    return configWithHost;
  } catch (e) {
    return null;
  }
}, { promise: true });

export const fetchAllViews = async (rootPath = '') => {
  try {
    const config = await Api.request('geolayer/scene/');
    const allViews = JSON.parse(JSON.stringify(config.results).replace(/"\/api(\/[^"]+)"/g, `"${Api.host}$1"`));
    return allViews.map(({
      name,
      slug,
      custom_icon: customIcon,
    }) => ({
      id: `nav-${slug}`,
      label: name,
      href: rootPath ? `/${rootPath}/${slug}` : `/${slug}`,
      icon: customIcon || defaultIcon,
    }));
  } catch (e) {
    // eslint-disable-next-line no-console
    console.log(e);
    return [];
  }
};

export default { fetchViewConfig, fetchAllViews };
