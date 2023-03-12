import React from 'react';
import PropTypes from 'prop-types';
import searchService, { getExtent, getSearchParamFromProperty } from '@terralego/core/modules/Visualizer/services/search';
import nunjucks from 'nunjucks';
import isEqual from 'react-fast-compare';
import debounce from 'debounce';

import Loading from './Loading';

const env = nunjucks.configure();
env.addFilter('formatNumber', value => new Intl.NumberFormat().format(value));

const getAggregationValue = (aggregation, match = []) => {
  if (!aggregation) return null;

  const { value, buckets } = aggregation;

  if (buckets) {
    return buckets
      .filter(({ key }) => match.includes(key))
      .reduce((total, { doc_count: docCount }) => total + docCount, 0);
  }

  return value;
};

export class WidgetSynthesis extends React.Component {
  static propTypes = {
    items: PropTypes.arrayOf(PropTypes.shape({
      name: PropTypes.string,
      type: PropTypes.string,
      field: PropTypes.string,
      format: PropTypes.string,
    })),
  }

  static defaultProps = {
    items: [],
  }

  state = {
    values: {},
  }

  debouncedLoad = debounce(() => this.load(), 1000);

  componentDidMount () {
    const { map } = this.props;
    if (!map) return;
    this.debouncedLoad();
    map.on('moveend', this.debouncedLoad);
    map.on('zoomend', this.debouncedLoad);
  }

  componentDidUpdate ({
    filters: prevFilters,
    query: prevQuery,
    visibleBoundingBox: prevVisibleBoundingBox,
  }) {
    const { filters, query, visibleBoundingBox } = this.props;
    if (!isEqual(filters, prevFilters)
      || query !== prevQuery
      || visibleBoundingBox !== prevVisibleBoundingBox) {
      this.resetValues();
      this.debouncedLoad();
    }
  }

  componentWillUnmount () {
    this.isUnmount = true;
    const { map } = this.props;
    if (!map) return;
    map.off('moveend', this.debouncedLoad);
    map.off('zoomend', this.debouncedLoad);
  }

  resetValues () {
    this.setState({ values: {} });
  }

  async load () {
    const {
      items,
      filters,
      form,
      layer,
      query,
      map,
      visibleBoundingBox,
      displayedLayer: { baseEsQuery = {} } = {},
    } = this.props;

    if (!map) return;
    const boundingBox = getExtent(map, visibleBoundingBox);

    const aggregations = items.map(({ name, type, field }) => ({
      name, type, field,
    }));

    const properties = {
      ...Object.keys(filters).reduce((all, key) => ({
        ...all,
        ...getSearchParamFromProperty(filters, form, key),
      }), {}),
    };

    const data = await searchService.search({
      index: layer,
      query,
      properties,
      boundingBox,
      aggregations,
      baseQuery: baseEsQuery,
      size: 0,
    });


    if (data.status !== 200) {
      return;
    }

    if (this.isUnmount) return;

    const values = items.reduce((prev, { name, value }) => ({
      ...prev,
      [name]: getAggregationValue(data.aggregations[name], value),
    }), {});

    this.setState({ values });
  }

  formatValue ({ name, label = name, template }) {
    const { values: { [name]: rawValue } } = this.state;
    const withValue = value => ({ label, value });
    if (rawValue === undefined) {
      return withValue(Loading);
    }

    if (!template) {
      return withValue(rawValue);
    }

    return withValue(
      nunjucks.renderString(template, { value: rawValue }),
    );
  }

  render () {
    const { items } = this.props;
    const values = items.map(item => this.formatValue(item));

    return (
      <div className="widget-synthesis">
        {values.map(({ label, value: Value }) => (
          <div
            className="widget-synthesis__item"
            key={`${label}${Value}`}
          >
            {typeof Value === 'function'
              ? <Value />
              : (
                <div
                  className="widget-synthesis__value"
                  // Value could contains html that should be rendered
                  // eslint-disable-next-line react/no-danger
                  dangerouslySetInnerHTML={{ __html: Value }}
                />
              )}
            <div className="widget-synthesis__label">{label}</div>
          </div>
        ))}
      </div>
    );
  }
}

export default WidgetSynthesis;
