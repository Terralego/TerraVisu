import React from 'react';
import renderer from 'react-test-renderer';
import PartnerPage from './PartnerPage';

it('should render correctly', () => {
  const tree = renderer.create(
    <PartnerPage />,
  ).toJSON();
  expect(tree).toMatchSnapshot();
});
