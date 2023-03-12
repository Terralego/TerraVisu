import React from 'react';
import ResizeObserver from 'resize-observer-polyfill';
import PropTypes from 'prop-types';
import debounce from 'debounce';

const VisibleBoundingBox = ({ onChange, as: Component, children, ...props }) => {
  const ref = React.useRef();

  React.useEffect(() => {
    const debouncedOnChange = debounce(param => onChange(param), 500);
    const ro = new ResizeObserver(([{ target }]) => {
      debouncedOnChange(target.getBoundingClientRect());
    });
    ro.observe(ref.current);
  }, [onChange]);

  if (typeof children === 'function') {
    return (
      children({ ref })
    );
  }

  return (
    <Component ref={ref} {...props}>
      {children}
    </Component>
  );
};

VisibleBoundingBox.propTypes = {
  onChange: PropTypes.func,
  as: PropTypes.string,
};

VisibleBoundingBox.defaultProps = {
  onChange () {},
  as: 'div',
};

export default VisibleBoundingBox;
