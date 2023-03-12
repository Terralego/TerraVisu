import React from 'react';
import { Card } from '@blueprintjs/core';

import FormProfile from './FormProfile';

import './styles.scss';

export const Profile = ({ match: { params: { id, token } } }) => (
  <div className="profile">
    <Card className="profile__content">
      <FormProfile
        create={(id && token) && {
          id,
          token,
        }}
      />
    </Card>
  </div>
);

export default Profile;
