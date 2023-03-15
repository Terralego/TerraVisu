import React from 'react';
import renderer from 'react-test-renderer';
import { shallow } from 'enzyme';

import VisibleBoundingBox from './BoundingBoxObserver';

jest.mock('resize-observer-polyfill', () => jest.fn(callback => (
  {
    observe: jest.fn(() => {
      callback([{ target: { getBoundingClientRect: jest.fn() } }]);
    }),
    disconnect: jest.fn(),
  }
)));

jest.mock('debounce', () => fn => () => fn());

it('should render if children is a component', () => {
  const tree = renderer.create((
    <VisibleBoundingBox>
      <div>foo</div>
    </VisibleBoundingBox>
  )).toJSON();
  expect(tree).toMatchSnapshot();
});


it('should render if children is a function', () => {
  const bar = () => <p>bar</p>;
  const tree = renderer.create((
    <VisibleBoundingBox>
      {bar}
    </VisibleBoundingBox>
  )).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should call onChange', () => {
  const onChange = jest.fn();
  shallow(
    <VisibleBoundingBox onChange={onChange}>
      <div>foo</div>
    </VisibleBoundingBox>,
  );
  expect(onChange.toHaveBeenCalled);
});

it('should call disconnect when component will unmount', () => {
  const wrapper = shallow(
    <VisibleBoundingBox>
      <div>foo</div>
    </VisibleBoundingBox>,
  );
  wrapper.unmount();
});
