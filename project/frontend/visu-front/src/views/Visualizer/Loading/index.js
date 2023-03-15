import React from 'react';
import './styles.scss';

export const Loading = () => (
  <div className="visuPlaceholder">
    <div className="visuPlaceholder__layerstree">
      <div className="visuPlaceholder__layerstree-appName skeleton" />
      <div className="visuPlaceholder__layerstree-title skeleton" />
      <div className="visuPlaceholder__layerstree-group">
        <div className="visuPlaceholder__layerstree-group-title skeleton" />
        <ul className="visuPlaceholder__layerstree-group-items">
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
        </ul>
      </div>
      <div className="visuPlaceholder__layerstree-group">
        <div className="visuPlaceholder__layerstree-group-title skeleton" />
        <ul className="visuPlaceholder__layerstree-group-items">
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
        </ul>
      </div>
      <div className="visuPlaceholder__layerstree-group">
        <div className="visuPlaceholder__layerstree-group-title skeleton" />
        <ul className="visuPlaceholder__layerstree-group-items">
          <li className="visuPlaceholder__layerstree-group-item skeleton" />
        </ul>
      </div>
    </div>
  </div>
);

export default Loading;
