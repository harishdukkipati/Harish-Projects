import React from 'react';

function SeasonStats({ seasonStats }) {

  console.log('DONKEYYYYY');
  console.log(seasonStats);

  const calculatePer36 = (stat, mp) => {
    if (!mp || mp === 0) return 'N/A';
    return ((stat / mp) * 36).toFixed(1);
  };

  return (
    <div className="season-stats-wrapper">
        {Object.entries(
  seasonStats.reduce((acc, stat) => {
    const key = `${stat.Season} - ${stat.League}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(stat);
    return acc;
  }, {})
).map(([key, entries], idx) => {
  const [seasonLabel, leagueLabel] = key.split(' - ');
  const season = entries[0]; // Assuming one entry per season-league combo

  return (
    <div key={idx} className="season-block">
      <h3>{seasonLabel} Season Averages – {leagueLabel}</h3>
      <table className="stats-table">
        <thead>
          <tr>
            <th>GP</th>
            <th>GS</th>
            <th>MPG</th>
            <th>PTS</th>
            <th>REB</th>
            <th>AST</th>
            <th>STL</th>
            <th>BLK</th>
            <th>TO</th>
            <th>FG%</th>
            <th>3P%</th>
            <th>FT%</th>
            <th>eFG%</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{season.GP ?? 'N/A'}</td>
            <td>{season.GS ?? 'N/A'}</td>
            <td>{season.MP ?? 'N/A'}</td>
            <td>{season.PTS ?? 'N/A'}</td>
            <td>{((season.ORB ?? 0) + (season.DRB ?? 0)).toFixed(1)}</td>
            <td>{season.AST ?? 'N/A'}</td>
            <td>{season.STL ?? 'N/A'}</td>
            <td>{season.BLK ?? 'N/A'}</td>
            <td>{season.TOV ?? 'N/A'}</td>
            <td>{season['FG%'] ?? 'N/A'}</td>
            <td>{season['3P%'] ?? 'N/A'}</td>
            <td>{season.FTP ?? 'N/A'}</td>
            <td>{season['eFG%'] ?? 'N/A'}</td>
          </tr>
          <tr>
              <td colSpan={3}><strong>Per 36 Minutes</strong></td>
              <td>{calculatePer36(season.PTS, season.MP)}</td>
              <td>{calculatePer36((season.ORB ?? 0) + (season.DRB ?? 0), season.MP)}</td>
              <td>{calculatePer36(season.AST, season.MP)}</td>
              <td>{calculatePer36(season.STL, season.MP)}</td>
              <td>{calculatePer36(season.BLK, season.MP)}</td>
              <td>{calculatePer36(season.TOV, season.MP)}</td>
              <td> {season['FG%'] ?? 'N/A'} </td> {/* FG% - skip */}
              <td>{season['3P%'] ?? 'N/A'} </td> {/* 3P% - skip */}
              <td>{season.FTP ?? 'N/A'}</td> {/* FT% - skip */}
              <td>{season['eFG%'] ?? 'N/A'}</td> {/* eFG% - skip */}
            </tr>
        </tbody>
      </table>
    </div>
  );
})}
</div>
  );
}

export default SeasonStats;