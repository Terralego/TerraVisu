import React from 'react';
import { Helmet } from 'react-helmet';

const Head = ({
  settings: {
    theme: {
      styles,
    } = {},
    favicon,
    title,
  } = {},
}) => (
  <Helmet>
    <title>{title}</title>
    {styles && styles.map(link => <link key={link} rel="stylesheet" type="text/css" href={link} />)}
    {favicon && <link rel="icon" href={favicon} />}
  </Helmet>
);
export default Head;
