import { useState } from 'react';
import ScoutingReport from './PlayerMeasurments';
import PlayerStatistics from './PlayerStatistics';
import ScoutingReports from './ScoutingReport'; 
import { Button } from '@mui/material';
import './PlayerProfile.css';

function PlayerProfile() {
  const [activeTab, setActiveTab] = useState(null); 

  return (
    <div className="profile-page">
      <ScoutingReport />

      {/* Tab buttons */}
      <div className="tab-buttons">
        <Button
          variant={activeTab === 'stats' ? 'contained' : 'outlined'}
          color="warning"
          onClick={() => setActiveTab('stats')}
        >
          Player Stats
        </Button>
        <Button
          variant={activeTab === 'reports' ? 'contained' : 'outlined'}
          color="warning"
          onClick={() => setActiveTab('reports')}
        >
          Scouting Reports
        </Button>
      </div>

      {/* Tab content (render only when tab is selected) */}
      <div className="tab-content">
        {activeTab === 'stats' && <PlayerStatistics />}
        {activeTab === 'reports' && <ScoutingReports />}
      </div>
    </div>
  );
}

export default PlayerProfile;
