import React from 'react';
import renderer from 'react-test-renderer';
import Main from '.';

jest.mock('./Header', () => () => <div>Header</div>);
jest.mock('./Content', () => () => <div>Content</div>);

it('should render correctly', () => {
  const tree = renderer.create(<Main />).toJSON();
  expect(tree).toMatchSnapshot();
});
