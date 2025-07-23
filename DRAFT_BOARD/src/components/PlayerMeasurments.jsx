import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import data from '../data/intern_project_data.json';
import processPlayerMeasurements from '../utils/processPlayerMeasurments';
import { useNavigate } from 'react-router-dom';
import './PlayerProfile.css';
import { Button } from '@mui/material';

function ScoutingReport() {
  const navigate = useNavigate();
  const { playerId } = useParams();
  const [player, setPlayer] = useState(null);

  useEffect(() => {
    const enrichedPlayer = processPlayerMeasurements(playerId, data.bio, data.measurements);
    setPlayer(enrichedPlayer);
  }, [playerId]);

  if (!player) return <div>Loading...</div>;

  const measurements = [
    { label: 'Wingspan',          value: player.measurements.wingspan + ' inches'},
    { label: 'Reach',             value: player.measurements.reach + ' inches'},
    { label: 'Max Vertical',      value: player.measurements.maxVertical + ' inches'},
    { label: 'No Step Vertical',  value: player.measurements.noStepVertical + ' inches'},
    { label: 'Body Fat',          value: player.measurements.bodyFat ?? 'N/A' },
    { label: 'Hand Length',       value: player.measurements.handLength + ' inches'},
    { label: 'Hand Width',        value: player.measurements.handWidth + ' inches'},
    { label: 'Agility',           value: player.measurements.agility + ' seconds'},
    { label: 'Sprint',            value: player.measurements.sprint + ' seconds'},
    { label: 'Shuttle Left',      value: player.measurements.shuttleLeft  ?? 'N/A' },
    { label: 'Shuttle Right',     value: player.measurements.shuttleRight ?? 'N/A' },
    { 
      label: 'Shuttle Best', 
      value: player.measurements.shuttleBest != null 
        ? player.measurements.shuttleBest + ' seconds' 
        : 'N/A'
    }
  ];

  return (
    <>
      <div className="profile-card">
  <div className="profile-header-banner">
    <div className="player-banner">
    <img
  src={!player.photoUrl ? 'https://cdn.nba.com/headshots/nba/latest/1040x760/1641750.png' : player.photoUrl}
  alt={player.name}
  className='banner-image'
  onError={(e) => {
    e.target.onerror = null;
    e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/1641750.png';
  }}
/>
      <div className="banner-info">
        <h1 className="player-name">
          <span className="first">{player.firstName}</span>{' '}
          <span className="last">{player.lastName}</span>
        </h1>
        <p><strong>Height:</strong> {player.height} inches</p>
        <p><strong>Weight:</strong> {player.weight} lbs</p>
        <p><strong>Team:</strong> {player.currentTeam}</p>
        <p><strong>League:</strong> {player.league}</p>
      </div>
    </div>
    <div className="add-report-button-wrapper">
      <Button 
        variant="contained"
        color="primary"
        onClick={() => navigate('/BigBoard')}
        className="add-report-button"
      >
        Back to Big Board
      </Button>
    </div>
  </div>


        <div className="measurements-grid">
          {measurements.map((m) => (
            <div key={m.label}>
              <strong>{m.label}:</strong> {m.value}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export default ScoutingReport;