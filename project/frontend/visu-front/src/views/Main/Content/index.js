import React, { Suspense, lazy } from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import compose from '@terralego/core/utils/compose';

import withEnv from '../../../config/withEnv';
import { connectSettings } from '../Provider/context';
import Loading from '../../../components/Loading';
import AppName from '../AppName';
import VisualizerLoading from '../../Visualizer/Loading';

const Profile = lazy(() => import('../../Profile'));
const Error404 = lazy(() => import('../../Error404'));
const Visualizer = lazy(() => import('../../Visualizer'));


const Content = ({
  env: { VIEW_ROOT_PATH = 'view', DEFAULT_VIEWNAME = 'rechercher' },
  settings: { title, version, credits = 'credits', theme: { logoUrl } = {} },
}) => {
  const exportCallback = React.useCallback((xlsx, sheet) => {
    xlsx.utils.sheet_add_aoa(sheet, [
      [],
      [credits],
    ], { origin: -1 });
    const wholeRange = xlsx.utils.decode_range(sheet['!ref']);
    const lastCell = sheet[xlsx.utils.encode_cell({
      c: 0,
      r: wholeRange.e.r,
    })];
    lastCell.l = {
      Target: logoUrl,
      Tooltip: title,
    };
  }, [credits, logoUrl, title]);

  return (
    <div className="main__content">
      <Switch>
        <Route path="/create-account/:id/:token">
          <Suspense fallback={<Loading />}>
            <Profile />
          </Suspense>
        </Route>
        <Route path={`/${VIEW_ROOT_PATH}/not-found`}>
          <p>Vue non trouvée :(</p>
        </Route>
        <Route path={`/${VIEW_ROOT_PATH}/:viewName`}>
          <Suspense fallback={<VisualizerLoading />}>
            <Visualizer
              renderHeader={<AppName title={title} version={version} />}
              exportCallback={exportCallback}
            />
          </Suspense>
        </Route>
        <Route path="/">
          <Redirect to={`/${VIEW_ROOT_PATH}/${DEFAULT_VIEWNAME}`} />
        </Route>
        <Route render={() => (
          <Suspense fallback={<VisualizerLoading />}>
            <Error404 />
          </Suspense>
        )}
        />
      </Switch>
    </div>
  );
};

export default compose(
  withEnv,
  connectSettings('settings'),
)(Content);
