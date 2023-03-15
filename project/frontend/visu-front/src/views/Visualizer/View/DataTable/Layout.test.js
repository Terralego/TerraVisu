import React from 'react';
import renderer from 'react-test-renderer';
import Layout from './Layout';

it('should render correctly hidden', () => {
  const tree = renderer.create((
    <Layout>
      <p>Foo</p>
    </Layout>
  )).toJSON();
  expect(tree).toMatchSnapshot();
});

it('should render correctly visible', () => {
  const tree = renderer.create((
    <Layout visible>
      <p>Foo</p>
    </Layout>
  )).toJSON();
  expect(tree).toMatchSnapshot();
});
