import {
  fetchAllViews,
  fetchViewConfig,
} from './visualizer';

it('should fetch view\'s config', async done => {
  const response = {
    layersTree: [],
    map: {
      customStyle: {
        sources: [],
        layers: [],
      },
    },
  };
  const fetched = {
    json: () => response,
  };
  global.fetch = jest.fn(() => fetched);

  const resp = await fetchViewConfig('some/url/foo');

  expect(resp).toEqual(response);

  done();
});

it('should fail to fetch view\'s config if response not suitable ', async done => {
  const response = {};
  const fetched = {
    json: () => response,
  };
  global.fetch = jest.fn(() => fetched);

  const resp = await fetchViewConfig('some/url/bar');

  expect(resp).toBe(null);

  done();
});

it('should fetch views', async done => {
  const response = {
    results: [],
  };
  const fetched = {
    json: () => response,
  };
  global.fetch = jest.fn(() => fetched);

  const resp = await fetchAllViews('some/url/foo');

  expect(resp).toEqual(response.results);

  done();
});

it('should fail to fetch views', async done => {
  const fetched = {
    status: 404,
    statusText: 'not found',
  };
  global.fetch = jest.fn(() => fetched);

  try {
    const resp = await fetchAllViews('some/url/foo');
    expect(resp).toEqual([]);
  } catch (e) {
    expect(e.message).toBe('not found');
  }

  done();
});
