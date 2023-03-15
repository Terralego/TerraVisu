import React from 'react';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import Table from '@terralego/core/modules/Table';
import searchService, {
  getExtent,
  getSearchParamFromProperty,
} from '@terralego/core/modules/Visualizer/services/search';
import debounce from 'debounce';

import { extractColumns, prepareData, exportSpreadsheet } from './dataUtils';
import Header from './Header';

import './styles.scss';

const sort = (data, column = 0) => data
  .map((line, index) => ({
    value: line[column], index,
  }))
  .sort((a, b) => a.value - b.value)
  .map(({ index }) => data[index]);

export class DataTable extends React.Component {
  static propTypes = {
    displayedLayer: PropTypes.shape({
      filters: PropTypes.shape({
        layer: PropTypes.string.isRequired,
        exportable: PropTypes.bool,
        table: PropTypes.shape({
          title: PropTypes.string,
        }),
        fields: PropTypes.arrayOf(PropTypes.shape({
          value: PropTypes.string.isRequired,
          label: PropTypes.string.isRequired,
          exportable: PropTypes.bool,
          display: PropTypes.bool, // default true
        })),
      }),
    }),
    isTableVisible: PropTypes.bool,
    query: PropTypes.string,
    filters: PropTypes.shape({
      // anyKey: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    }),
  };

  static defaultProps = {
    displayedLayer: undefined,
    isTableVisible: true,
    query: '',
    filters: {},
  };

  state = {
    columns: null,
    results: [],
    resultsTotal: 0,
    loading: true,
    selectedFeatures: [],
  };

  debouncedLoadResults = debounce(() => this.loadResults(), 500);

  componentDidMount () {
    const { displayedLayer } = this.props;
    if (displayedLayer) {
      this.debouncedLoadResults();
    }
  }

  shouldComponentUpdate ({ isTableVisible }) {
    const {
      isTableVisible: prevTableVisible,
    } = this.props;

    if (isTableVisible !== prevTableVisible || isTableVisible) {
      return true;
    }
    return false;
  }

  componentDidUpdate ({
    displayedLayer: {
      filters: { layer: prevLayer, fields: prevFields } = {},
      state: { filters: prevFilters } = {},
    } = {},
    query: prevQuery,
  }, {
    extent: prevExtent,
  }) {
    const {
      displayedLayer,
      displayedLayer: {
        filters: { layer, fields } = {},
        state: { filters } = {},
      } = {},
      query,
    } = this.props;

    const { extent } = this.state;

    if (displayedLayer) {
      if (layer !== prevLayer
       || prevFields !== fields) {
        this.resetColumns();
      }

      if (layer !== prevLayer
        || query !== prevQuery
        || filters !== prevFilters
        || (extent && this.extentChanged())
        || prevFields !== fields
        || extent !== prevExtent) { // This test must keep at last position
        this.debouncedLoadResults();
      }
    }
  }

  resize = () => this.setState(({ full: prevFull }) => {
    const full = !prevFull;

    if (full) {
      setTimeout(() => this.setState({ full, isResizing: false }), 300);
      return { isResizing: true };
    }
    setTimeout(() => this.setState({ isResizing: false }), 300);
    return { full, isResizing: true };
  })

  toggleExtent = () => this.setState(({ extent }) => ({ extent: !extent }));

  onSelection = selection => {
    const { features } = this.state;

    if (!features) return;
    const { results } = this.state;
    const selectedFeatures = selection.map(id => ({ _id: results[id][0] }));
    this.setState({ selectedFeatures });
  }

  exportDataAction = () => {
    const {
      displayedLayer: {
        label: name,
        filters: { fields = [] } = {},
      },
      exportCallback,
    } = this.props;

    if (!fields) return;

    const { columns, results } = this.state;

    // Find out which column (indexes) are exportable
    const exportableColumnIndexes = columns.reduce((store, { value }, index) => {
      const fieldConfig = fields.find(field => field.value === value);
      const { exportable = false } = fieldConfig || {};
      return exportable ? [...store, index] : store;
    }, []);

    // Create array of column header texts
    const columnLabels = columns.map(({ value, label = value }) => label);

    // Go through each line and keep only exportable columns
    const data = [columnLabels, ...results]
      .map(dataLine => exportableColumnIndexes.map(index => dataLine[index]));

    exportSpreadsheet({
      name,
      data,
      callback: exportCallback,
    });
  };

  resetColumns () {
    this.setState({ columns: null });
  }

  extentChanged () {
    const { map, visibleBoundingBox } = this.props;
    const prevExtent = this.prevExtent || [[], []];
    this.prevExtent = getExtent(map, visibleBoundingBox);
    const [[a, b], [c, d]] = prevExtent;
    const [[aa, bb], [cc, dd]] = this.prevExtent;
    return !(a === aa && b === bb && c === cc && d === dd);
  }

  async loadResults () {
    const {
      displayedLayer: {
        filters: { layer, fields, form } = {},
        state: { filters = {} } = {},
        baseEsQuery,
      } = {},
      query,
      map,
      visibleBoundingBox,
    } = this.props;
    const { columns, extent } = this.state;

    this.setState({ loading: true });

    this.prevExtent = extent && getExtent(map, visibleBoundingBox);
    const boundingBox = this.prevExtent;

    const properties = {
      ...Object.keys(filters).reduce((all, key) => ({
        ...all,
        ...getSearchParamFromProperty(filters, form, key),
      }), {}),
    };

    const resp = await searchService.search({
      index: layer,
      query,
      properties,
      boundingBox,
      baseQuery: baseEsQuery,
      include: fields && fields.reduce((all, { value }) => {
        const interpolation = value.match(/\{[^}]+\}/g);
        return [
          ...all,
          ...interpolation
            ? interpolation.map(match => match.match(/\{([^}]+)\}/)[1])
            : [value],
        ];
      }, []),
    });

    const { hits: { hits, total: { value: resultsTotal } } } = resp;
    const newColumns = columns || extractColumns(fields, hits);

    const results = sort(prepareData(newColumns, hits, {
      decimals: 1,
    }));

    this.setState({ features: hits, results, resultsTotal, columns: newColumns, loading: false });
  }

  render () {
    const { displayedLayer, isTableVisible } = this.props;

    const {
      label,
      compare,
      filters: {
        layer,
        table: { title } = {},
        exportable,
        fields = [],
      } = {},
    } = displayedLayer || {};

    const haveExportableField = fields.some(({ exportable: exportableField }) => exportableField);
    const showExportButton = exportable && haveExportableField;

    const {
      columns, results, resultsTotal,
      loading, full, isResizing,
      extent, selectedFeatures,
    } = this.state;
    const firstLoading = !columns && loading;

    const { resize, toggleExtent, onSelection, exportDataAction } = this;
    return (
      <div className={classnames({
        'data-table': true,
        'data-table--visible': isTableVisible,
      })}
      >
        <div
          className={classnames({
            'table-container': true,
            'table-container--visible': isTableVisible,
            'table-container--is-resizing': isResizing,
            'table-container--full': full,
          })}
        >
          {isTableVisible && (
            <Table
              columns={columns || []}
              data={results || []}
              onSelection={onSelection}
              Header={props => (
                <Header
                  {...props}
                  resultsTotal={resultsTotal}
                  toggleExtent={toggleExtent}
                  extent={extent}
                  layer={layer}
                  compare={compare}
                  selectedFeatures={selectedFeatures || []}
                  loading={loading}
                  title={title || label}
                  full={full}
                  resize={resize}
                  exportData={showExportButton && exportDataAction}
                />
              )}
              locales={{
                sortAsc: 'Trier dans l\'ordre croissant',
                sortDesc: 'Trier dans l\'ordre décroissant',
              }}
              loading={firstLoading}
            />
          )}
        </div>
      </div>
    );
  }
}

export default DataTable;
