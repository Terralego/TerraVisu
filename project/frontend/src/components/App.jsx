import React from 'react';
import Navbar from './navBar/navBar';
import Map from './map/Map';

function App() {
  fetch('/api/settings/').then((response) => response.json())
    .then((data) => {
      localStorage.setItem('settings', JSON.stringify(data));
    });

  return (
    <div className="App">
      <Navbar />
      <Map />
    </div>
  );
}

export default App;
