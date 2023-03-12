const { DJANGO_APP } = process.env;

export async function fetchEnv () {
  const rawEnv = await fetch(`${DJANGO_APP ? '/static' : ''}/env.json`);
  return rawEnv.json();
}

const promise = fetchEnv();

export const getEnv = () => promise;

export default { getEnv, fetchEnv };
