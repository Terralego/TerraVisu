import React, { useState } from 'react';
import PropTypes from 'prop-types';

import classNames from 'classnames';
import {
  Overlay,
  Classes,
} from '@blueprintjs/core';

import withDeviceSize from '@terralego/core/hoc/withDeviceSize';

import NavBarItemDesktop from '@terralego/core/components/NavBarItemDesktop';
import NavBarItemTablet from '@terralego/core/components/NavBarItemTablet';

import PartnerPage from './PartnerPage';

export const PartnerButton = ({ isMobileSized, isPhoneSized, ...props }) => {
  const [isOpen, setOpen] = useState(false);
  const NavBarItem = isMobileSized ? NavBarItemTablet : NavBarItemDesktop;

  return (
    <>
      <NavBarItem {...props} onClick={() => setOpen(true)} />
      <Overlay
        className={classNames(
          Classes.OVERLAY_SCROLL_CONTAINER,
          Classes.LIGHT,
          'modal-mentions-legales',
        )}
        isOpen={isOpen}
        onClose={() => setOpen(false)}
      >
        <div
          className={classNames(
            Classes.CARD,
            Classes.ELEVATION_4,
          )}
        >
          <PartnerPage />
        </div>
      </Overlay>
    </>
  );
};

PartnerButton.propTypes = {
  isMobileSized: PropTypes.bool,
  isPhoneSized: PropTypes.bool,
};

PartnerButton.defaultProps = {
  isMobileSized: false,
  isPhoneSized: false,
};


export default withDeviceSize()(PartnerButton);
