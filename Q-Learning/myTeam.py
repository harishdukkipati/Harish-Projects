from pacai.agents.capture.capture import CaptureAgent
import random

class AlphaBetaAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
        self.treedepth = 2
        self.lastAttack = None

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        # Add any additional initialization code here.
        # print(self.distancer._distances)

    def chooseAction(self, gameState):
        """
        Choose an action based on alpha-beta search.
        """

        def maxValue(gamestate, depth, alpha, beta):
            goodvalue = float('-inf')
            goodaction = None
            for action in gamestate.getLegalActions(self.index):
                if alpha >= beta:
                    break
                successor = gamestate.generateSuccessor(self.index, action)
                value, thing = values(successor, depth, 1, alpha, beta)
                if value > goodvalue:
                    goodvalue = value
                    goodaction = action

                alpha = max(alpha, goodvalue)

            return goodvalue, goodaction

        def minValue(gamestate, depth, turn, alpha, beta):
            goodvalue = float('inf')
            goodaction = None
            opponentIndices = self.getOpponents(gameState)
            for action in gamestate.getLegalActions(opponentIndices[turn - 1]):
                if alpha >= beta:
                    break
                successor = gamestate.generateSuccessor(opponentIndices[turn - 1], action)
                if turn == 3 - 1:
                    value, thing = values(successor, depth - 1, 0, alpha, beta)
                else:
                    value, thing = values(successor, depth, turn + 1, alpha, beta)

                if value < goodvalue:
                    goodvalue = value
                    goodaction = action

                beta = min(beta, goodvalue)
            return goodvalue, goodaction

        def values(gamestate, depth, turn, alpha, beta):
            if depth == 0 or gamestate.isWin() or gamestate.isLose():
                return self.evaluate(gamestate), None
            if turn == 0:
                return maxValue(gamestate, depth, alpha, beta)
            else:
                return minValue(gamestate, depth, turn, alpha, beta)
        value, action = values(gameState, self.treedepth, 0, float('-inf'), float('inf'))
        return action

    def evaluate(self, gameState):
        currentPosition = gameState.getAgentPosition(self.index)

        food = self.getFood(gameState).asList()
        distanceToFood = [self.getMazeDistance(currentPosition, foods) for foods in food]

        if len(food) <= 2:
            return float('inf')
        # Used to discourage taking the same path the defender is
        # blocking at the boundary, might remove
        defenderIndices = self.getOpponents(gameState)
        for defenderIndex in defenderIndices:
            if gameState.getAgentState(self.index).isGhost() and self.getMazeDistance(
                    currentPosition, gameState.getAgentPosition(defenderIndex)) <= 4:
                return -(random.choice(distanceToFood))

        return -min(distanceToFood) / len(food) * 0.1 + self.getScore(gameState) * 100
class DefendAlphaBetaAgent(CaptureAgent):

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
        self.treedepth = 2
        self.lastAttack = None

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        # Add any additional initialization code here.

    def chooseAction(self, gameState):

        def maxValue(gamestate, depth, alpha, beta):
            goodvalue = float('-inf')
            goodaction = None
            for action in gamestate.getLegalActions(self.index):
                if alpha >= beta:
                    break
                successor = gamestate.generateSuccessor(self.index, action)
                value, thing = values(successor, depth, 1, alpha, beta)
                if value > goodvalue:
                    goodvalue = value
                    goodaction = action

                alpha = max(alpha, goodvalue)

            return goodvalue, goodaction

        def minValue(gamestate, depth, turn, alpha, beta):
            goodvalue = float('inf')
            goodaction = None
            opponentIndices = self.getOpponents(gameState)
            for action in gamestate.getLegalActions(opponentIndices[turn - 1]):
                if alpha >= beta:
                    break
                successor = gamestate.generateSuccessor(opponentIndices[turn - 1], action)
                if turn == len(opponentIndices) - 1:
                    value, thing = values(successor, depth - 1, 0, alpha, beta)
                else:
                    value, thing = values(successor, depth, turn + 1, alpha, beta)

                if value < goodvalue:
                    goodvalue = value
                    goodaction = action

                beta = min(beta, goodvalue)
            return goodvalue, goodaction

        def values(gamestate, depth, turn, alpha, beta):
            if depth == 0 or gamestate.isWin() or gamestate.isLose():
                return self.evaluate(gamestate), None
            if turn == 0:
                return maxValue(gamestate, depth, alpha, beta)
            else:
                return minValue(gamestate, depth, turn, alpha, beta)
        value, action = values(gameState, self.treedepth, 0, float('-inf'), float('inf'))
        return action

    def evaluate(self, gameState):
        currentPosition = gameState.getAgentPosition(self.index)

        defenderIndices = self.getOpponents(gameState)
        foods = self.getFoodYouAreDefending(gameState).asList()

        baitScore = float('inf')

        for defenderIndex in defenderIndices:
            defenderPosition = gameState.getAgentPosition(defenderIndex)
            defenderState = gameState.getAgentState(defenderIndex)

            if defenderState.isPacman():
                if self.lastAttack is None:
                    self.lastAttack = defenderIndex
                baitScore = -self.getMazeDistance(currentPosition, defenderPosition) - 1000000000
                break
            else:
                if self.lastAttack is not None:
                    defenderPosi = gameState.getAgentPosition(self.lastAttack)
                    min_distance = float('inf')
                    targetFood = None

                    for food in foods:
                        distance = self.getMazeDistance(defenderPosi, food)
                        if distance < min_distance:
                            min_distance = distance
                            targetFood = food
                    baitScore = -(self.getMazeDistance(currentPosition, targetFood))
                else:
                    min_distance = float('inf')
                    targetFood = None

                    for food in foods:
                        distance = self.getMazeDistance(defenderPosition, food)
                        if distance < min_distance:
                            min_distance = distance
                            targetFood = food

                    baitScore = -(self.getMazeDistance(currentPosition, targetFood))

        if gameState.getAgentState(self.index).isPacman():
            baitScore = float('-inf')

        return baitScore

def createTeam(firstIndex, secondIndex, isRed,
               first=AlphaBetaAgent,
               second=DefendAlphaBetaAgent):
    """
    This function should return a list of two agents that will form the capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """

    return [
        first(firstIndex),
        second(secondIndex),
    ]
