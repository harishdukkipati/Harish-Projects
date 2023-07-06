"""
In this file, you will implement generic search algorithms which are called by Pacman agents.
"""

from pacai.util.stack import Stack
from pacai.util.queue import Queue
from pacai.util.priorityQueue import PriorityQueue

def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first [p 85].

    Your search algorithm needs to return a list of actions that reaches the goal.
    Make sure to implement a graph search algorithm [Fig. 3.7].

    To get started, you might want to try some of these simple commands to
    understand the search problem that is being passed in:
    ```
    print("Start: %s" % (str(problem.startingState())))
    print("Is the start a goal?: %s" % (problem.isGoal(problem.startingState())))
    print("Start's successors: %s" % (problem.successorStates(problem.startingState())))
    ```
    """

    # *** Your Code Here ***
    node = problem.startingState()
    explored = set()

    stateDic = {}

    stack = Stack()

    stack.push((node, []))

    while not stack.isEmpty():
        node, path = stack.pop()
        if problem.isGoal(node):
            return path
        if node not in explored:
            explored.add(node)
            for child, action, cost in problem.successorStates(node):
                if child not in explored:
                    stateDic[child] = node
                    stack.push((child, path + [action]))
    return []

def breadthFirstSearch(problem):
    """
    Search the shallowest nodes in the search tree first. [p 81]
    """

    # *** Your Code Here ***
    node = problem.startingState()
    explored = set()

    stateDic = {}

    queue = Queue()

    queue.push((node, []))

    while not queue.isEmpty():
        node, path = queue.pop()
        if problem.isGoal(node):
            return path
        if node not in explored:
            explored.add(node)
            for child, action, cost in problem.successorStates(node):
                if child not in explored:
                    stateDic[child] = node
                    queue.push((child, path + [action]))
    return []

def uniformCostSearch(problem):
    """
    Search the node of least total cost first.
    """

    # *** Your Code Here ***
    node = problem.startingState()
    explored = set()

    stateDic = {}
    stateDic[node] = None

    pqueue = PriorityQueue()
    pqueue.push((node, [], 0), 0)

    while not pqueue.isEmpty():
        node, path, cost = pqueue.pop()
        if problem.isGoal(node):
            return path
        if node not in explored:
            explored.add(node)
            for child, action, step_cost in problem.successorStates(node):
                if child not in explored:
                    stateDic[child] = node
                    child_cost = cost + step_cost
                    pqueue.push((child, path + [action], child_cost), child_cost)
    return []

def aStarSearch(problem, heuristic):
    """
    Search the node that has the lowest combined cost and heuristic first.
    """

    # *** Your Code Here ***
    node = problem.startingState()
    explored = set()

    stateDic = {}
    stateDic[node] = None

    g_cost = {node: 0}
    f_cost = {node: heuristic(node, problem)}

    pqueue = PriorityQueue()
    pqueue.push((node, [], 0), f_cost[node])

    while not pqueue.isEmpty():
        node, path, cost = pqueue.pop()
        if problem.isGoal(node):
            return path
        if node not in explored:
            explored.add(node)
            for child_node, action, step_cost in problem.successorStates(node):
                if child_node not in explored:
                    stateDic[child_node] = node
                    child_g_cost = g_cost[node] + step_cost
                    if child_node not in g_cost or child_g_cost < g_cost[child_node]:
                        g_cost[child_node] = child_g_cost
                        f_cost[child_node] = child_g_cost + heuristic(child_node, problem)
                        pqueue.push((child_node, path + [action], child_g_cost), f_cost[child_node])
    return []
