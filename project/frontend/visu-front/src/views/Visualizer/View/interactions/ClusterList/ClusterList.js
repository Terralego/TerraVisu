import React, { useState } from 'react';
import { Menu, InputGroup, Button } from '@blueprintjs/core';

import './styles.scss';

const ID = '_id';

export const ClusterList = ({ features, onClick, clusterLabel }) => {
  const [query, setQuery] = useState('');
  const filteredFeatures = features
    .filter(({ properties: { [clusterLabel]: label } }) =>
      !query
      || label.toLowerCase().match(query.toLowerCase()));
  return (
    <div className="clustered-features-list">
      {features.length > 10 && (
        <InputGroup
          leftIcon="search"
          className="clustered-features-list__search"
          value={query}
          onChange={({ target: { value } }) => setQuery(value)}
          rightElement={query && (
            <Button
              className="clustered-features-list__clear-search"
              icon="cross"
              onClick={() => setQuery('')}
              minimal
            />
          )}
        />
      )}
      <div className="clustered-features-list__scroll">
        <Menu>
          {filteredFeatures.map(feature => (
            <Menu.Item
              key={feature.properties[ID]}
              onClick={() => onClick(feature)}
              text={feature.properties[clusterLabel]}
            />
          ))}
        </Menu>
      </div>
    </div>
  );
};

export default ClusterList;
