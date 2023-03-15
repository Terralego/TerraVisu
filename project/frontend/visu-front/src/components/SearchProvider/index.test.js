import React from 'react';
import renderer from 'react-test-renderer';

import SearchProvider from './SearchProvider';

it('should render', () => {
  const tree = renderer.create((
    <SearchProvider>
      <div>foo</div>
    </SearchProvider>
  )).toJSON();
  expect(tree).toMatchSnapshot();
});
