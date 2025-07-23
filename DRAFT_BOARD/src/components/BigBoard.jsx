import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import processPlayerRankings from '../utils/processPlayerRankings';
import data from '../data/intern_project_data.json';
import './BigBoard.css';
import MavsLogo from '../assets/Dallas_Mavericks_logo.svg.png';

function BigBoard() {
  const [players, setPlayers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('All');

  

  useEffect(() => {
    const finalPlayers = processPlayerRankings(data.bio, data.scoutRankings);
    setPlayers(finalPlayers);
  }, []);

  const teams = ['All', ...new Set(players.map(p => p.currentTeam).filter(Boolean))];

  const filteredPlayers = players.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTeam = selectedTeam === 'All' || p.currentTeam === selectedTeam;
    return matchesSearch && matchesTeam;
  });

  return (
    <div className='draft-hub-container'>
    <header className="hub-header">
  <div className="hub-header-inner">
    <div className="hub-header-top">
      <img src={MavsLogo} alt="Mavs Logo" className="mavs-logo" />
      <h1 className="title">NBA Draft Hub</h1>
    </div>
    <div className="filters">
      <input
        type="text"
        placeholder="Search players..."
        className="search-input"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <select
        className="team-filter"
        value={selectedTeam}
        onChange={(e) => setSelectedTeam(e.target.value)}
      >
        {teams.map(team => (
          <option key={team} value={team}>{team}</option>
        ))}
      </select>
    </div>
  </div>
</header>

      <div className='player-list'>
        {filteredPlayers.map(p => (
          <Link
            to={`/player/${p.playerId}`}
            key={p.playerId}
            className='player-card'
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
<img
  src={!p.photoUrl ? 'https://cdn.nba.com/headshots/nba/latest/1040x760/1641750.png' : p.photoUrl}
  alt={p.name}
  className='player-photo'
  onError={(e) => {
    e.target.onerror = null;
    e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/1641750.png';
  }}
/>
            <div className='player-info'>
              <h2>{p.rank}. {p.name}</h2>
              <p><strong>Team:</strong> {p.currentTeam}</p>
              <div>
                <strong>Scout Ranks:</strong>
                <ul>
  {Object.entries(p.scoutRanks)
    .sort(([a, ra], [b, rb]) => (ra ?? Infinity) - (rb ?? Infinity))
    .map(([scout, rank]) => {
      const isHigh = rank != null && rank < p.rank;
      const isLow = rank != null && rank > p.rank;
      const className = isHigh
        ? 'highlight-up'
        : isLow
        ? 'highlight-down'
        : '';

      return (
        <li key={scout} className={className}>
          {rank == null ? `${scout}: N/A` : `${scout}: ${rank} ${isHigh ? '🔼' : isLow ? '🔽' : ''}`}
        </li>
      );
    })}
</ul>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default BigBoard;
