function processPlayerStatistic(playerId, bio, game_logs) {
    console.log(playerId);
    const player = bio.find(p => p.playerId === parseInt(playerId));
    const game_log = game_logs.filter(g => g.playerId === parseInt(playerId));
  
    const result = {
      ...player,
      game_logs: game_log,
    };
  
    console.log(result);
    return result;
  }
  
  function processSeasonStatistics(playerId, bio, season_logs) {
    console.log(playerId);
    const player = bio.find(p => p.playerId === parseInt(playerId));
    const season_log = season_logs.filter(s => s.playerId === parseInt(playerId));
  
    const result = {
      ...player,
      season_logs: season_log,
    };
  
    console.log(result);
    return result;
  }
  
  export { processPlayerStatistic, processSeasonStatistics };
  