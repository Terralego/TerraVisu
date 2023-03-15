import React from 'react';
import renderer from 'react-test-renderer';
import { PartnerButton } from './PartnerButton';

jest.mock('@terralego/core/components/NavBarItemTablet', () => () => <div className="container">NavBarItemTablet</div>);
jest.mock('@terralego/core/components/NavBarItemDesktop', () => () => <div className="container">NavBarItemDesktop</div>);

it('should render correctly in mode desktop', () => {
  const tree = renderer.create(
    <PartnerButton />,
  ).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should render correctly in mode mobile', () => {
  const tree = renderer.create(
    <PartnerButton isMobileSized />,
  ).toJSON();
  expect(tree).toMatchSnapshot();
});
