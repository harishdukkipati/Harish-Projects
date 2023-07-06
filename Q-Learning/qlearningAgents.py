from pacai.agents.learning.reinforcement import ReinforcementAgent
from pacai.util import reflection
import random
from pacai.util.probability import flipCoin

class QLearningAgent(ReinforcementAgent):
    """
    A Q-Learning agent.

    Some functions that may be useful:

    `pacai.agents.learning.reinforcement.ReinforcementAgent.getAlpha`:
    Get the learning rate.

    `pacai.agents.learning.reinforcement.ReinforcementAgent.getDiscountRate`:
    Get the discount rate.

    `pacai.agents.learning.reinforcement.ReinforcementAgent.getEpsilon`:
    Get the exploration probability.

    `pacai.agents.learning.reinforcement.ReinforcementAgent.getLegalActions`:
    Get the legal actions for a reinforcement agent.

    `pacai.util.probability.flipCoin`:
    Flip a coin (get a binary value) with some probability.

    `random.choice`:
    Pick randomly from a list.

    Additional methods to implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Compute the action to take in the current state.
    With probability `pacai.agents.learning.reinforcement.ReinforcementAgent.getEpsilon`,
    we should take a random action and take the best policy action otherwise.
    Note that if there are no legal actions, which is the case at the terminal state,
    you should choose None as the action.

    `pacai.agents.learning.reinforcement.ReinforcementAgent.update`:
    The parent class calls this to observe a state transition and reward.
    You should do your Q-Value update here.
    Note that you should never call this function, it will be called on your behalf.

    DESCRIPTION: <Write something here so we know what you did.>
    Used the Q learning formula from lecture 15
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

        # You can initialize Q-values here.
        self.qvalues = {}

    def update(self, state, action, next_state, reward):
        d = self.getDiscountRate()
        a = self.getAlpha()
        val = self.getValue(next_state)
        qValue = self.getQValue(state, action)
        sample = reward + d * val
        self.qvalues[(state, action)] = ((1 - a) * qValue) + (a * sample)

    def getAction(self, state):
        if flipCoin(1 - self.getEpsilon()):
            return self.getPolicy(state)
        return random.choice(self.getLegalActions(state))

    def getQValue(self, state, action):
        """
        Get the Q-Value for a `pacai.core.gamestate.AbstractGameState`
        and `pacai.core.directions.Directions`.
        Should return 0.0 if the (state, action) pair has never been seen.
        """
        if state in self.qvalues:
            return self.q_values[(state, action)]
        return 0.0

    def getValue(self, state):
        """
        Return the value of the best action in a state.
        I.E., the value of the action that solves: `max_action Q(state, action)`.
        Where the max is over legal actions.
        Note that if there are no legal actions, which is the case at the terminal state,
        you should return a value of 0.0.

        This method pairs with `QLearningAgent.getPolicy`,
        which returns the actual best action.
        Whereas this method returns the value of the best action.
        """
        legal_actions = self.getLegalActions(state)
        if not legal_actions:
            return 0.0
        max_val = float('-inf')

        for action in legal_actions:
            q_val = self.qvalues.get((state, action), 0.0)
            if q_val >= max_val:
                max_val = q_val

        return max_val

        return 0.0

    def getPolicy(self, state):
        """
        Return the best action in a state.
        I.E., the action that solves: `max_action Q(state, action)`.
        Where the max is over legal actions.
        Note that if there are no legal actions, which is the case at the terminal state,
        you should return a value of None.

        This method pairs with `QLearningAgent.getValue`,
        which returns the value of the best action.
        Whereas this method returns the best action itself.
        """
        legal_actions = self.getLegalActions(state)
        action = None
        if not legal_actions:
            return action

        max_val = float('-inf')
        best_actions = []

        for action in legal_actions:
            q_val = self.qvalues.get((state, action), 0.0)
            if q_val > max_val:
                max_val = q_val
                best_actions = [action]
            elif q_val == max_val:
                best_actions.append(action)

        return random.choice(best_actions)

        return None

class PacmanQAgent(QLearningAgent):
    """
    Exactly the same as `QLearningAgent`, but with different default parameters.
    """

    def __init__(self, index, epsilon = 0.05, gamma = 0.8, alpha = 0.2, numTraining = 0, **kwargs):
        kwargs['epsilon'] = epsilon
        kwargs['gamma'] = gamma
        kwargs['alpha'] = alpha
        kwargs['numTraining'] = numTraining

        super().__init__(index, **kwargs)

    def getAction(self, state):
        """
        Simply calls the super getAction method and then informs the parent of an action for Pacman.
        Do not change or remove this method.
        """

        action = super().getAction(state)
        self.doAction(state, action)

        return action

class ApproximateQAgent(PacmanQAgent):
    """
    An approximate Q-learning agent.

    You should only have to overwrite `QLearningAgent.getQValue`
    and `pacai.agents.learning.reinforcement.ReinforcementAgent.update`.
    All other `QLearningAgent` functions should work as is.

    Additional methods to implement:

    `QLearningAgent.getQValue`:
    Should return `Q(state, action) = w * featureVector`,
    where `*` is the dotProduct operator.

    `pacai.agents.learning.reinforcement.ReinforcementAgent.update`:
    Should update your weights based on transition.

    DESCRIPTION: <Write something here so we know what you did.>
    Got the Q value for each state-action
    pair. Updated the weights by first calculating the correction(difference), and
    plugging into the formula given in Question 9.
    """

    def __init__(self, index,
            extractor = 'pacai.core.featureExtractors.IdentityExtractor', **kwargs):
        super().__init__(index, **kwargs)
        self.featExtractor = reflection.qualifiedImport(extractor)

        # You might want to initialize weights here.
        self.weights = {}

    def update(self, state, action, nextState, reward):
        feature = self.featExtractor.getFeatures(self, state, action)
        discount = self.getDiscountRate()
        d = (reward + discount * self.getValue(nextState)) - self.getQValue(state, action)
        if not self.weights:
            for features in feature:
                self.weights[features] = 1
        for key in self.weights.keys():
            self.weights[key] += (self.alpha * d * feature[key])

    def getQValue(self, state, action):
        feature = self.featExtractor.getFeatures(self, state, action)
        qValue = 0.0
        for feat, value in feature.items():
            if feat in self.weights:
                qValue += value * self.weights[feat]
        return qValue

    def final(self, state):
        """
        Called at the end of each game.
        """

        # Call the super-class final method.
        super().final(state)

        # Did we finish training?
        if self.episodesSoFar == self.numTraining:
            # You might want to print your weights here for debugging.
            print("Weights = ", self.weights)
            # *** Your Code Here ***
