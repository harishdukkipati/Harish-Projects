import random
from pacai.agents.base import BaseAgent
from pacai.agents.search.multiagent import MultiAgentSearchAgent
from pacai.core import distance
from pacai.core.directions import Directions

class ReflexAgent(BaseAgent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.
    You are welcome to change it in any way you see fit,
    so long as you don't touch the method headers.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def getAction(self, gameState):
        """
        You do not need to change this method, but you're welcome to.

        `ReflexAgent.getAction` chooses among the best options according to the evaluation function.

        Just like in the previous project, this method takes a
        `pacai.core.gamestate.AbstractGameState` and returns some value from
        `pacai.core.directions.Directions`.
        """

        # Collect legal moves.
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions.
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices)  # Pick randomly among the best.

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current `pacai.bin.pacman.PacmanGameState`
        and an action, and returns a number, where higher numbers are better.
        Make sure to understand the range of different values before you combine them
        in your evaluation function.
        """
        # Useful information you can extract.
        # newPosition = successorGameState.getPacmanPosition()
        # oldFood = currentGameState.getFood()
        # newGhostStates = successorGameState.getGhostStates()
        # newScaredTimes = [ghostState.getScaredTimer() for ghostState in newGhostStates]

        # *** Your Code Here ***
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        score = successorGameState.getScore()
        foodList = currentGameState.getFood().asList()
        pacmanPos = successorGameState.getPacmanPosition()

        closestDist = min([distance.manhattan(pacmanPos, food) for food in foodList])
        furthestDist = max([distance.manhattan(pacmanPos, food) for food in foodList])

        score -= closestDist
        score -= furthestDist

        for ghost in successorGameState.getGhostStates():
            ghostDistances = [distance.manhattan(pacmanPos, ghost.getPosition())]

        if min(ghostDistances) < 3:
            score -= 1000000

        numFoods = currentGameState.getNumFood()
        if successorGameState.getNumFood() < numFoods:
            score += 1000

        return score

class MinimaxAgent(MultiAgentSearchAgent):
    """
    A minimax agent.

    Here are some method calls that might be useful when implementing minimax.

    `pacai.core.gamestate.AbstractGameState.getNumAgents()`:
    Get the total number of agents in the game

    `pacai.core.gamestate.AbstractGameState.getLegalActions`:
    Returns a list of legal actions for an agent.
    Pacman is always at index 0, and ghosts are >= 1.

    `pacai.core.gamestate.AbstractGameState.generateSuccessor`:
    Get the successor game state after an agent takes an action.

    `pacai.core.directions.Directions.STOP`:
    The stop direction, which is always legal, but you may not want to include in your search.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the minimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def getAction(self, gameState):
        eval = self.getEvaluationFunction()
        num_agents = gameState.getNumAgents()
        tree_depth = self.getTreeDepth()

        def max_value(state, agent_idx, depth):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = float('-inf')
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                v = max(v, min_value(next_state, agent_idx + 1, depth))
            return v

        def min_value(state, agent_idx, depth):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = float('inf')
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                if agent_idx == num_agents - 1:
                    v = min(v, max_value(next_state, 0, depth + 1))
                else:
                    v = min(v, min_value(next_state, agent_idx + 1, depth))
            return v

        actions = gameState.getLegalActions(0)
        best_score = float('-inf')
        best_action = None
        for action in actions:
            next_state = gameState.generateSuccessor(0, action)
            score = min_value(next_state, 1, 0)
            if score > best_score:
                best_score = score
                best_action = action
            elif score == best_score and random.choice([True, False]):
                best_action = action
        return best_action
class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    A minimax agent with alpha-beta pruning.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the minimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
        self.depth = 3

    def getAction(self, gameState):
        eval = self.getEvaluationFunction()
        num_agents = gameState.getNumAgents()
        tree_depth = self.getTreeDepth()

        def max_value(state, agent_idx, depth, alpha, beta):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = float('-inf')
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                v = max(v, min_value(next_state, agent_idx + 1, depth, alpha, beta))
                if v >= beta:
                    return v
                alpha = max(v, alpha)
            return v

        def min_value(state, agent_idx, depth, alpha, beta):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = float('inf')
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                if agent_idx == num_agents - 1:
                    v = min(v, max_value(next_state, 0, depth + 1, alpha, beta))
                    if v <= alpha:
                        return v
                    beta = min(v, beta)
                else:
                    v = min(v, min_value(next_state, agent_idx + 1, depth, alpha, beta))
                    if v <= alpha:
                        return v
                    beta = min(v, beta)
            return v

        actions = gameState.getLegalActions(0)
        best_score = float('-inf')
        best_action = None
        for action in actions:
            next_state = gameState.generateSuccessor(0, action)
            score = min_value(next_state, 1, 0, float('-inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_action = action
            elif score == best_score and random.choice([True, False]):
                best_action = action
        return best_action


class ExpectimaxAgent(MultiAgentSearchAgent):
    """
    An expectimax agent.

    All ghosts should be modeled as choosing uniformly at random from their legal moves.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the expectimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
        self.depth = 3

    def getAction(self, gameState):
        eval = self.getEvaluationFunction()
        num_agents = gameState.getNumAgents()
        tree_depth = self.getTreeDepth()

        def max_value(state, agent_idx, depth):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = float('-inf')
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                v = max(v, min_value(next_state, agent_idx + 1, depth))
            return v

        def min_value(state, agent_idx, depth):
            if depth == tree_depth or state.isOver():
                return eval(state)
            v = 0
            actions = state.getLegalActions(agent_idx)
            for action in actions:
                next_state = state.generateSuccessor(agent_idx, action)
                if agent_idx == num_agents - 1:
                    v += max_value(next_state, 0, depth + 1)
                else:
                    v += min_value(next_state, agent_idx + 1, depth)
            return v / len(actions)

        actions = gameState.getLegalActions(0)
        actions.remove(Directions.STOP)
        best_score = float('-inf')
        best_action = None
        for action in actions:
            next_state = gameState.generateSuccessor(0, action)
            score = min_value(next_state, 1, 0)
            if score > best_score:
                best_score = score
                best_action = action
            elif score == best_score and random.choice([True, False]):
                best_action = action
        return best_action

def betterEvaluationFunction(currentGameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable evaluation function.

    DESCRIPTION: <write something here so we know what you did>
    """
    pacmanPos = currentGameState.getPacmanPosition()
    foodList = currentGameState.getFood().asList()
    ghostStates = currentGameState.getGhostStates()
    capsules = currentGameState.getCapsules()

    foodDist = float("inf")
    for food in foodList:
        dist = distance.manhattan(pacmanPos, food)
        foodDist = min(dist, foodDist)

    ghostDist = float("inf")
    for ghost in ghostStates:
        dist = distance.manhattan(pacmanPos, ghost.getPosition())
        ghostDist = min(ghostDist, dist)

    capsuleDist = float("inf")
    for capsule in capsules:
        dist = distance.manhattan(pacmanPos, capsule)
        capsuleDist = min(capsuleDist, dist)

    score = currentGameState.getScore()

    if ghostDist < 2:
        score -= 100000

    else:
        score += 1000.0 / (foodDist + 1)
        score += 500.0 / ghostDist
        score += 500.0 / (capsuleDist + 1)
        score += 50 * len(foodList)

    return score

    return currentGameState.getScore()

class ContestAgent(MultiAgentSearchAgent):
    """
    Your agent for the mini-contest.

    You can use any method you want and search to any depth you want.
    Just remember that the mini-contest is timed, so you have to trade off speed and computation.

    Ghosts don't behave randomly anymore, but they aren't perfect either -- they'll usually
    just make a beeline straight towards Pacman (or away if they're scared!)

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
