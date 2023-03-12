module.exports = {
  root: true,
  extends: 'makina',
  rules: {
    'jsx-a11y/label-has-associated-control': ['error', {
      controlComponents: ['InputGroup'],
    }],
  },
};
