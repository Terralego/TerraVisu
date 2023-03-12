import React from 'react';
import renderer from 'react-test-renderer';
import Content from '.';

jest.mock('react-router-dom', () => ({
  Route: () => null,
  Switch: ({ children }) => children,
  Redirect: () => null,
}));

it('should render correctly', () => {
  const tree = renderer.create(<Content />).toJSON();
  expect(tree).toMatchSnapshot();
});
