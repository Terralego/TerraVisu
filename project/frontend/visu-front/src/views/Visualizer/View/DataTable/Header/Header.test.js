import React from 'react';
import renderer from 'react-test-renderer';
import Header from './Header';


jest.mock('@terralego/core/modules/Table/components/ColumnsSelector', () =>
  props => (
    <p {...props}>ColumnsSelector</p>
  ));
it('should render correctly', () => {
  const tree = renderer.create((
    <Header
      title="foo"
      resultsTotal={42}
    />
  )).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should render correctly with no result', () => {
  const tree = renderer.create((
    <Header
      title="foo"
      resultsTotal={1}
    />
  )).toJSON();
  expect(tree).toMatchSnapshot();
});
