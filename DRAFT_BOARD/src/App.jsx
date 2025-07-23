import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import BigBoard from './components/BigBoard';
import PlayerProfile from './components/PlayerProfile'

function App() {
  return (
    <>
        <Routes>
          <Route path="/" element={<BigBoard />} /> 
          <Route path="/BigBoard" element={<BigBoard />} />
          <Route path="/player/:playerId" element={<PlayerProfile />} />
        </Routes>
    </>
  )
}

export default App
