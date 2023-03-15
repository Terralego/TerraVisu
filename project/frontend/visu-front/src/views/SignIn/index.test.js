import React from 'react';
import renderer from 'react-test-renderer';
import { SignInView } from '.';

jest.mock('@terralego/core/modules/Auth', () => ({
  LoginForm: () => <div>LoginForm Mock</div>,
  connectAuthProvider: () => () => null,
}));

describe('rendering', () => {
  it('should render correctly when auth is false', () => {
    const tree = renderer.create((
      <SignInView authenticated={false} logoutAction={() => null} />
    )).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('should render correctly when auth is true', () => {
    const tree = renderer.create((
      <SignInView authenticated logoutAction={() => null} />
    )).toJSON();
    expect(tree).toMatchSnapshot();
  });
});
