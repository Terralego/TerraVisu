import React from 'react';
import Navbar from './navBar/navBar';
import Map from './map/Map';
import './App.css';

async function fetchSettings() {
  const response = await fetch('/api/settings/');
  const data = await response.json();
  return data;
}

export default function App() {
  fetchSettings().then((data) => {
    localStorage.removeItem('settings');
    localStorage.setItem('settings', JSON.stringify(data));
  });

  return (
    <div className="App">
      <Navbar />
      <Map />
    </div>
  );
}
