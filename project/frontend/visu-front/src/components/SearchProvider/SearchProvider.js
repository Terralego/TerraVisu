import search from '@terralego/core/modules/Visualizer/services/search';
import PropTypes from 'prop-types';

export const SearchProvider = ({ children, env: { API_HOST } }) => {
  search.host = API_HOST.replace(/api$/, 'elasticsearch');
  return children;
};

SearchProvider.propTypes = {
  children: PropTypes.element.isRequired,
  env: PropTypes.shape({
    API_HOST: PropTypes.string,
  }),
};

SearchProvider.defaultProps = {
  env: {
    API_HOST: 'auran.org/api',
  },
};

export default SearchProvider;
