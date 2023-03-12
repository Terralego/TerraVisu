import { fetchEnv } from './env';

it('should fetch env config', async () => {
  const response = {
    API_HOST: 'http://foo/api',
    VIEW_ROOT_PATH: 'visualiser',
    DEFAULT_VIEWNAME: 'population',
  };

  window.fetch = jest.fn().mockImplementationOnce(() => Promise.resolve({
    json: () => response,
  }));
  const resp = await fetchEnv();
  expect(resp).toBe(response);
});
