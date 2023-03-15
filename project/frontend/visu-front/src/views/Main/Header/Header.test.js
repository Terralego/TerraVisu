import React from 'react';
import { act, create } from 'react-test-renderer';

import { Header } from './Header';

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: text => text,
  }),
}));

jest.mock('@terralego/core/components/MainMenu', () => props => <div {...props} />);
jest.mock('@terralego/core/components/LoginButton', () => props => <div {...props} />);

jest.mock('./PartnerButton', () => () => 'PartnerButton');

jest.mock('../../../services/visualizer', () => (
  {
    fetchAllViews: jest.fn(() => [{
      id: 'foo',
      label: 'Foo',
      href: '/foo',
      icon: 'path/to/iconFoo',
    }, {
      id: 'bar',
      label: 'Bar',
      href: '/bar',
      icon: 'path/to/iconBar',
    }]),
  }
));

it('should render correctly', () => {
  let tree;
  act(() => {
    tree = create(
      <Header />,
    );
  });
  expect(tree.toJSON()).toMatchSnapshot();
});

it('should render correctly with header open in mobile view', () => {
  let tree;
  act(() => {
    tree = create(
      <Header
        isMobileSized
        isHeaderOpen
      />,
    );
  });
  expect(tree.toJSON()).toMatchSnapshot();
});

it('should render correctly with header close in mobile view', () => {
  let tree;
  act(() => {
    tree = create(
      <Header
        location={{ pathname: '/' }}
        env={{ VIEW_ROOT_PATH: '' }}
        settings={{}}
        isMobileSized
        isHeaderOpen={false}
      />,
    );
  });
  expect(tree.toJSON()).toMatchSnapshot();
});

/* it('should open navbar in mobile', () => {
  const toggleHeader = jest.fn();
  const wrapper = shallow(<Header toggleHeader={toggleHeader} />);
  const instance = wrapper.instance();
  const target = '<div class="main__header__target--test" />';

  instance.containerRef.current = {
    target,
    contains: () => true,
  };
  instance.listener({ target });

  expect(instance.props.toggleHeader).toHaveBeenCalledWith();
}); */
