
export default function processPlayerRankings(bio, scoutRankings) {
    const playerData = {}
    scoutRankings.forEach(entry => {
        const {playerId, ...scoutScores } = entry;
        let total = 0;
        let count = 0 ;
        for (const [scout, scores] of Object.entries(scoutScores)) {
            if (scores !== null) {
                total += scores;
                count++;
            }
        }
        let avgScore = null;
        if (count > 0) {
            avgScore = total/count 
        }

        playerData[playerId] = {
            playerId,
            avgScore,
            scoutRanks: scoutScores,
        }
    });

    const sortedPlayersWithRank = Object.values(playerData) 
        .filter(i => i.avgScore != null)
        .sort((a, b) => {
            if (a.avgScore != b.avgScore) { 
                return a.avgScore - b.avgScore;
            }
            const aStd = stdDev(Object.values(a.scoutRanks).filter(r => r != null));
            const bStd = stdDev(Object.values(b.scoutRanks).filter(r => r != null));
            return aStd - bStd
        })
        .map((player, index) => ({
            ...player,
            rank: index + 1,
        }));
    
    console.log(sortedPlayersWithRank);

    const biomap = {};
    bio.forEach(player => {
        biomap[player.playerId] = player
    });

    console.log(biomap)


    const finalPlayers = sortedPlayersWithRank.map(player => ({
        ...biomap[player.playerId],
        playerId: player.playerId,
        ...player,
      }));
    
      console.log(finalPlayers)

    return finalPlayers;
    
}

function stdDev(arr) {
    if (!arr.length) return 0;
  
    const mean = arr.reduce((sum, val) => sum + val, 0) / arr.length;
    const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
  
    return Math.sqrt(variance);
  
}

