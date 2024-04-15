/*
 * Copyright (C) 2022-2024 David C. Harrison. All right reserved.
 *
 * You may not use, distribute, publish, or modify this code without
 * the express written permission of the copyright holder.
 */

import {BrowserRouter, Route, Routes} from 'react-router-dom';

import Home from './components/Home';
import Login from './components/Login';
import Messages from './components/messages';

/**
 * @return {*} JSX Component
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/home" exact element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/messages/:channelId" element={<Messages/>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
