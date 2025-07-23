import React from 'react';
import './PlayerProfile.css';

function GameLogs({ gameLogs }) {
  if (!gameLogs || gameLogs.length === 0) {
    return <p>No game logs available.</p>;
  }

  const seasons = Array.from(new Set(gameLogs.map(g => g.season)));

  return (
    <>
      {seasons.map(season => {
        const seasonGames = gameLogs.filter(g => g.season === season);

        const totals = seasonGames.reduce((acc, game) => {
          acc.fgm += game.fgm || 0;
          acc.fga += game.fga || 0;
          acc.ftm += game.ftm || 0;
          acc.fta += game.fta || 0;
          acc.reb += game.reb || 0;
          acc.ast += game.ast || 0;
          acc.stl += game.stl || 0;
          acc.blk += game.blk || 0;
          acc.tov += game.tov || 0;
          acc.pf += game.pf || 0;
          acc.plusMinus += game.plusMinus || 0;
          acc.pts += game.pts || 0;
          return acc;
        }, {
          fgm: 0, fga: 0, ftm: 0, fta: 0,
          reb: 0, ast: 0, stl: 0, blk: 0,
          tov: 0, pf: 0, plusMinus: 0, pts: 0
        });

        const fgPct = totals.fga > 0 ? ((totals.fgm / totals.fga) * 100).toFixed(1) + '%' : 'N/A';
        const ftPct = totals.fta > 0 ? ((totals.ftm / totals.fta) * 100).toFixed(1) + '%' : 'N/A';
        const plusMinus = totals.plusMinus > 0 ? '+' + totals.plusMinus : totals.plusMinus;

        return (
          <div key={season} className="season-block">
            <h3>{season} Season</h3>
            <table className="stats-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Opponent</th>
                  <th>MIN</th>
                  <th>FG</th>
                  <th>FG%</th>
                  <th>FT</th>
                  <th>FT%</th>
                  <th>REB</th>
                  <th>AST</th>
                  <th>STL</th>
                  <th>BLK</th>
                  <th>TO</th>
                  <th>PF</th>
                  <th>+/-</th>
                  <th>PTS</th>
                </tr>
              </thead>
              <tbody>
                {seasonGames.map((game, idx) => {
                  const pMinus = game.plusMinus > 0 ? '+' + game.plusMinus : game.plusMinus;
                  return (
                    <tr key={idx}>
                      <td>{new Date(game.date).toLocaleDateString()}</td>
                      <td>{game.opponent}</td>
                      <td>{game.timePlayed}</td>
                      <td>{game.fgm}/{game.fga}</td>
                      <td>{game["fg%"] ?? 'N/A'}</td>
                      <td>{game.ftm}/{game.fta}</td>
                      <td>{game.fta ? ((game.ftm / game.fta) * 100).toFixed(1) : 'N/A'}</td>
                      <td>{game.reb}</td>
                      <td>{game.ast}</td>
                      <td>{game.stl}</td>
                      <td>{game.blk}</td>
                      <td>{game.tov}</td>
                      <td>{game.pf}</td>
                      <td>{pMinus}</td>
                      <td>{game.pts}</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={3}><strong>Totals</strong></td>
                  <td><strong>{totals.fgm}/{totals.fga}</strong></td>
                  <td><strong>{fgPct}</strong></td>
                  <td><strong>{totals.ftm}/{totals.fta}</strong></td>
                  <td><strong>{ftPct}</strong></td>
                  <td><strong>{totals.reb}</strong></td>
                  <td><strong>{totals.ast}</strong></td>
                  <td><strong>{totals.stl}</strong></td>
                  <td><strong>{totals.blk}</strong></td>
                  <td><strong>{totals.tov}</strong></td>
                  <td><strong>{totals.pf}</strong></td>
                  <td><strong>{plusMinus}</strong></td>
                  <td><strong>{totals.pts}</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>
        );
      })}
    </>
  );
}

export default GameLogs;