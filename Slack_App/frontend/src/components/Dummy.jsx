/*
 * Copyright (C) 2022-2024 David C. Harrison. All right reserved.
 *
 * You may not use, distribute, publish, or modify this code without
 * the express written permission of the copyright holder.
 */
/*
 * *****************************************************
 * YOU CAN DELETE, BUT DO NOT MODIFY THIS FILE
 * *****************************************************
 */
import React from 'react';

/**
 * Fecthes dummy data from server.
 *
 * @param {function} setDummy set the dummy state
 */
function getDummy(setDummy) {
  fetch('http://localhost:3010/v0/dummy')
      .then((response) => {
        if (!response.ok) {
          throw response;
        }
        return response.json();
      })
      .then((json) => {
        setDummy(json.message);
      })
      .catch((error) => {
        setDummy(`ERROR: ${error.toString()}`);
      });
}

/**
 * Simple component with one state variable.
 *
 * @return {object} JSX
 */
function Dummy() {
  const [dummy, setDummy] = React.useState('Click the button!');
  return (
    <div>
      <h3>
        Click button to connect to the Backend dummy endpoint</h3>
      <button
        aria-label='get dummy'
        onClick={() => {
          getDummy(setDummy);
        }}
      >
        Get Dummy
      </button>
      <p/>
      <h3
        aria-label='dummy message'
      >
        {dummy}
      </h3>
    </div>
  );
}

export default Dummy;
