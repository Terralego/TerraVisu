import React from 'react';
import { useQuery } from 'react-query';
import Navbar from './navBar/navBar';
import Map from './map/Map';
import './App.css';

import fetchSettings from '../Api';

export default function App() {
  const { isLoading, error, data } = useQuery('settings', () => fetchSettings());
  if (isLoading) {
    return <span>Loading...</span>;
  }

  if (error) {
    return (
      <span>
        Error:
        {error.message}
      </span>
    );
  }

  return (
    <div className="App">
      <Navbar instance={data.instance} user={data.user} />
      <Map data />
    </div>
  );
}
