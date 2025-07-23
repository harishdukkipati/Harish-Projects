export default function processPlayerMeasurements(playerId, bio, measurements) {
    console.log(playerId)
    const player = bio.find(p => p.playerId === parseInt(playerId));
    const measurement = measurements.find(m => m.playerId === parseInt(playerId));
  
    const result = {
      ...player,
      measurements: measurement ? { ...measurement, playerId: undefined } : {},
    };
    console.log(result)

    return result
  }