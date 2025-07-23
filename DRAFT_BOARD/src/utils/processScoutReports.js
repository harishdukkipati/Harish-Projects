export default function processScoutReports(playerId, bio, scoutReports) {
    console.log(playerId);
    const player = bio.find(p => p.playerId === parseInt(playerId));
    const scout_Report = scoutReports.filter(g => g.playerId === parseInt(playerId));
  
    const result = {
      ...player,
      scoutReports: scout_Report,
    };
  
    console.log(result);
    return result;
} 