import React from 'react';
import renderer from 'react-test-renderer';
import DataTable from './DataTable';

jest.mock('@terralego/core/modules/Visualizer/services/search', () => ({
  search: jest.fn(() => ({
    hits: {
      hits: [{
        _source: {
          foo_prop: 'foo',
          bar_prop: 'bar',
        },
      }, {
        _source: {
          foo_prop: 'foo1',
          bar_prop: 'bar1',
        },
      }],
      total: { value: 2 },
    },
  })),
}));

jest.mock('debounce', () => fn => () => fn());

jest.mock('@terralego/core/modules/Table', () => props => <p {...props}>Table</p>);
jest.mock('@terralego/core/modules/Table/components/ColumnsSelector', () =>
  props => (
    <p {...props}>ColumnsSelector</p>
  ));

it('should render correctly', () => {
  const tree = renderer.create((
    <DataTable />
  )).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should render unvisible correctly', () => {
  const tree = renderer.create((
    <DataTable isTableVisible={false} />
  )).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should render correctly with results', async done => {
  const tree = renderer.create((
    <DataTable
      displayedLayer={{
        filters: {
          layer: 'foo',
          fields: [{
            label: 'Foo',
            value: 'foo_prop',
          }, {
            label: 'Bar',
            value: 'bar_prop',
          }],
        },
      }}
      resultsTotal={1}
    />
  ));

  await true;
  await true;
  await true;

  expect(tree.toJSON()).toMatchSnapshot();

  done();
});

it('should render a loader', () => {
  const tree = renderer.create((
    <DataTable
      displayedLayer={{
        filters: {
          layer: 'foo',
          fields: [{
            label: 'Foo',
            value: 'foo_prop',
          }, {
            label: 'Bar',
            value: 'bar_prop',
          }],
        },
      }}
      resultsTotal={1}
    />
  ));

  expect(tree.toJSON()).toMatchSnapshot();
});
