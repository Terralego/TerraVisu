import React, { useState, useEffect, useCallback, useMemo } from 'react';

import classnames from 'classnames';
import withDeviceSize from '@terralego/core/hoc/withDeviceSize';
import { connectAuthProvider } from '@terralego/core/modules/Auth';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';
import { NavLink } from 'react-router-dom';

import MainMenu from '@terralego/core/components/MainMenu';
import LoginButton from '@terralego/core/components/LoginButton';
import { fetchAllViews } from '../../../services/visualizer';

import PartnerButton from './PartnerButton';

import './styles.scss';

const getLinkProps = link => (
  !link.startsWith('http') && {
    link: {
      component: NavLink,
      linkProps: {
        hrefAttribute: 'to',
      },
    },
  }
);

export const Header = ({
  env: { VIEW_ROOT_PATH },
  isHeaderOpen,
  isMobileSized,
  toggleHeader,
  authenticated,
  settings: {
    theme: { logo = '', logoUrl = '/' } = {},
    extraMenuItems = [],
    allowUserRegistration,
  },
}) => {
  const [menu, setMenu] = useState([]);
  const { t } = useTranslation();

  const extraMenuItemsToMenu = useMemo(() => extraMenuItems.map(item => (
    { ...item, ...getLinkProps(item.href) }
  )), [extraMenuItems]);

  const generateMenu = useCallback(views => ({
    navHeader: {
      id: 'welcome',
      label: t('menu.home'),
      href: logoUrl,
      icon: logo,
      ...getLinkProps(logoUrl),
    },
    navItems: [
      views,
      extraMenuItemsToMenu,
      [{
        id: 'nav-partenaires',
        component: () => (
          <PartnerButton
            label={t('menu.informations')}
            icon="info-sign"
          />
        ),
      }, {
        id: 'nav-connexion',
        component: () => (
          <LoginButton
            icon={authenticated ? 'log-out' : 'log-in'}
            label={authenticated ? t('menu.logout') : t('menu.login')}
            className={authenticated ? 'log-out' : 'log-in'}
            translate={t}
            allowUserRegistration={allowUserRegistration}
          />
        ),
      }],
    ],
  }), [t, logoUrl, logo, extraMenuItemsToMenu, authenticated, allowUserRegistration]);


  useEffect(() => {
    let isMounted = true;

    const loadViewList = async () => {
      /** Load the view list and add it to base menu only if component mounted */
      const views = await fetchAllViews(VIEW_ROOT_PATH);
      if (!isMounted) return;
      const viewsToMenu = views.map(view => ({ ...view, ...getLinkProps(view.href) }));
      setMenu(generateMenu(viewsToMenu));
    };

    VIEW_ROOT_PATH && loadViewList();

    return () => {
      isMounted = false;
    };
  }, [VIEW_ROOT_PATH, generateMenu]);

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div
      className={classnames(
        'main__header',
        { 'main__header--mobile': isMobileSized },
        { 'main__header--mobile--open': isMobileSized && isHeaderOpen },
      )}
      onClick={() => toggleHeader()}
      role="button"
      tabIndex="-1"
    >
      <MainMenu {...menu} className="main__navbar" />
      {isMobileSized && !isHeaderOpen
        // eslint-disable-next-line jsx-a11y/click-events-have-key-events
        && <div className="main__header__target" role="button" tabIndex="-1" onClick={() => toggleHeader(false)} />
      }
    </div>
  );
};

Header.propTypes = {
  env: PropTypes.shape({
    VIEW_ROOT_PATH: PropTypes.string,
  }),
  isHeaderOpen: PropTypes.bool,
  isMobileSized: PropTypes.bool,
  toggleHeader: PropTypes.func,
  authenticated: PropTypes.bool,
  settings: PropTypes.shape({
    theme: PropTypes.shape({
      logo: PropTypes.string,
      logoUrl: PropTypes.string,
    }),
    extraMenuItems: PropTypes.array,
  }),
};

Header.defaultProps = {
  isHeaderOpen: false,
  isMobileSized: false,
  toggleHeader: () => {},
  authenticated: false,
  settings: {
    theme: {
      logo: '',
      logoUrl: '/',
    },
    extraMenuItems: [],
  },
  env: {
    VIEW_ROOT_PATH: '',
  },
};

export default withDeviceSize()(connectAuthProvider('authenticated')(Header));
