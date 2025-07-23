import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, TextField } from '@mui/material';
import data from '../data/intern_project_data.json';
import processScoutReports from '../utils/processScoutReports';
import './PlayerProfile.css';

function ScoutingReports() {
  const { playerId } = useParams();
  const [scoutReports, setScoutReports] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [newScoutName, setNewScoutName] = useState('');
  const [newReportText, setNewReportText] = useState('');

  useEffect(() => {
    const playerData = processScoutReports(playerId, data.bio, data.scoutingReports);
    setScoutReports(playerData?.scoutReports ?? []);
  }, [playerId]);

  const handleAddReport = () => {
    if (newScoutName.trim() && newReportText.trim()) {
      const newEntry = { scout: newScoutName, report: newReportText };
      setScoutReports(prev => [newEntry, ...prev]);
      setNewScoutName('');
      setNewReportText('');
      setShowForm(false);
    }
  };

  return (
    <div className="tab-content">
      {!showForm ? (
        <>
          <div className="add-report-button-wrapper">
            <Button
              variant="contained"
              color="primary"
              className="add-report-button"
              onClick={() => setShowForm(true)}
            >
              + Add Report
            </Button>
          </div>
  
          {scoutReports.length === 0 ? (
            <p>No scouting reports available.</p>
          ) : (
            scoutReports.map((entry, idx) => (
              <div key={idx} className="scouting-report-entry">
                <h4>{entry.scout}</h4>
                <p>{entry.report}</p>
              </div>
            ))
          )}
        </>
      ) : (
        <div className="form-wrapper">
          <h3 style={{ color: 'white', textAlign: 'center', marginBottom: '1rem' }}>
  New Scouting Report
</h3>
          <TextField
            label="Scout Name"
            value={newScoutName}
            onChange={(e) => setNewScoutName(e.target.value)}
            variant="outlined"
            fullWidth
            InputProps={{ style: { backgroundColor: 'white' } }}
            InputLabelProps={{
            shrink: false, 
            style: {
            opacity: newScoutName ? 0 : 1, 
          }
          }}
          style={{ marginBottom: '1rem' }}
          />

          <TextField
          label="Report"
          value={newReportText}
          onChange={(e) => setNewReportText(e.target.value)}
          variant="outlined"
          multiline
          rows={4}
          fullWidth
          InputProps={{ style: { backgroundColor: 'white' } }}
          InputLabelProps={{
          shrink: false,
          style: {
            opacity: newReportText ? 0 : 1,
          }
          }}
  style={{ marginBottom: '1rem' }}
/>

          <Button
            variant="contained"
            fullWidth
            style={{
              backgroundColor: 'white',
              color: 'black',
              fontWeight: 'bold'
            }}
            onClick={handleAddReport}
          >
            Submit
          </Button>
        </div>
      )}
    </div>
  );  
}

export default ScoutingReports;



