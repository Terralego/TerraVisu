import React from 'react';
import renderer from 'react-test-renderer';

import AppName from './AppName';

it('should render', () => {
  const tree = renderer.create(
    <AppName />,
  ).toJSON();
  expect(tree).toMatchSnapshot();
});
