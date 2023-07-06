from pacai.agents.learning.value import ValueEstimationAgent
from collections import defaultdict

class ValueIterationAgent(ValueEstimationAgent):
    """
    A value iteration agent.

    Make sure to read `pacai.agents.learning` before working on this class.

    A `ValueIterationAgent` takes a `pacai.core.mdp.MarkovDecisionProcess` on initialization,
    and runs value iteration for a given number of iterations using the supplied discount factor.

    Some useful mdp methods you will use:
    `pacai.core.mdp.MarkovDecisionProcess.getStates`,
    `pacai.core.mdp.MarkovDecisionProcess.getPossibleActions`,
    `pacai.core.mdp.MarkovDecisionProcess.getTransitionStatesAndProbs`,
    `pacai.core.mdp.MarkovDecisionProcess.getReward`.

    Additional methods to implement:

    `pacai.agents.learning.value.ValueEstimationAgent.getQValue`:
    The q-value of the state action pair (after the indicated number of value iteration passes).
    Note that value iteration does not necessarily create this quantity,
    and you may have to derive it on the fly.

    `pacai.agents.learning.value.ValueEstimationAgent.getPolicy`:
    The policy is the best action in the given state
    according to the values computed by value iteration.
    You may break ties any way you see fit.
    Note that if there are no legal actions, which is the case at the terminal state,
    you should return None.
    """

    def __init__(self, index, mdp, discountRate = 0.9, iters = 100, **kwargs):
        super().__init__(index, **kwargs)

        self.mdp = mdp
        self.discountRate = discountRate
        self.iters = iters
        self.values = defaultdict(int)
        for state in self.mdp.getStates():
            self.values[state] = self.getValue(state)
        for _ in range(self.iters):
            delta = 0.0
            tmp_values = defaultdict(int)
            for state in self.mdp.getStates():
                if self.mdp.isTerminal(state):
                    continue
                max_qval = float("-inf")
                for action in self.mdp.getPossibleActions(state):
                    qval = self.getQValue(state, action)
                    max_qval = max(max_qval, qval)
                if max_qval != float("-inf"):
                    tmp_values[state] = max_qval
                    delta = max(delta, abs(tmp_values[state] - self.values[state]))

            self.values = tmp_values
            if delta <= self.epsilon:
                break

    def getValue(self, state):
        """
        Return the value of the state (computed in __init__).
        """
        if self.mdp.isTerminal(state):
            return 0
        else:
            return self.values[state]

    def getAction(self, state):
        return self.getPolicy(state)

    def getPolicy(self, state):
        """
        Returns the policy at the state (no exploration).
        """
        if self.mdp.isTerminal(state):
            return None
        possibleActions = self.mdp.getPossibleActions(state)
        bestAction = None
        bestQvalue = float('-inf')
        for action in possibleActions:
            qvalue = self.getQValue(state, action)
            if qvalue > bestQvalue:
                bestQvalue = qvalue
                bestAction = action
        return bestAction

    def getQValue(self, state, action):
        qvalue = 0.0
        transitions = self.mdp.getTransitionStatesAndProbs(state, action)
        for nextState, prob in transitions:
            reward = self.mdp.getReward(state, action, nextState)
            qvalue += (prob * (reward + (self.discountRate * self.getValue(nextState))))
        return qvalue
