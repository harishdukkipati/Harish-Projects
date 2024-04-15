/*
#######################################################################
#
# Copyright (C) 2020-2024 David C. Harrison. All right reserved.
#
# You may not use, distribute, publish, or modify this code without
# the express written permission of the copyright holder.
#
#######################################################################
*/

import React from 'react';
import {useNavigate} from 'react-router-dom';
import './Login.css';

/**
 * @return {*} JSX Component
 */
function Login() {
  const [user, setUser] = React.useState({email: '', password: ''});
  const history = useNavigate();

  const handleInputChange = (event) => {
    const {value, name} = event.target;
    const u = user;
    u[name] = value;
    setUser(u);
  };

  console.log(user);
  const onSubmit = (event) => {
    event.preventDefault();
    fetch('http://localhost:3010/v0/login', {
      method: 'POST',
      body: JSON.stringify(user),
      headers: {
        'Content-Type': 'application/json',
      },
    })
        .then((res) => {
          if (!res.ok) {
            throw res;
          }
          return res.json();
        })
        .then((json) => {
          localStorage.setItem('user', JSON.stringify(json));
          history('/home');
        })
        .catch((err) => {
          alert('Error logging in, please try again');
        });
  };

  return (
    <div className = "container">
      <form onSubmit={onSubmit}>
        <h2 id='welcome'>SLACK ATTACK</h2>
        <input
          type="email"
          name="email"
          placeholder="EMail"
          onChange={handleInputChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          onChange={handleInputChange}
          required
        />
        <input type="submit" value="Sign In"/>
      </form>
    </div>
  );
}

export default Login;
