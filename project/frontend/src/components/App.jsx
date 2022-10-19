import React, { Component } from 'react';
import { render } from 'react-dom';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      data: [],
      loaded: false,
      placeholder: 'Loading',
    };
  }

  componentDidMount() {
    fetch('api/accounts/users/')
      .then((response) => {
        if (response.status > 400) {
          return this.setState(() => ({ placeholder: 'Something went wrong!' }));
        }
        return response.json();
      })
      .then((data) => {
        this.setState(() => ({
          data,
          loaded: true,
        }));
      });
  }

  render() {
    return (
      <ul>
        {this.state.data.map((user) => (
          <li key={user.id}>
            {user.email}
            {' '}
            -
            {user.uuid}
          </li>
        ))}
      </ul>
    );
  }
}

export default App;

const container = document.getElementById('app');
render(<App />, container);
