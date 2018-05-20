"""Depth first search and A-Star

See https://en.wikipedia.org/wiki/A*_search_algorithm
"""

from collections import deque
from heapq import heappush, heappop

_INFINITY = float('inf')


class _OpenSet(object):
    """An object for pushing on states and popping them off."""

    def push(self, state):
        """Put this state in this open set if possible.

        This will return whether or not the state can be pushed.
        """
        raise NotImplementedError

    def pop(self):
        """Remove and return a state. Raise an IndexError if the set is empty."""
        raise NotImplementedError

    def empty(self):
        """Return whether or not this open set is empty."""
        raise NotImplementedError


class _Stack(_OpenSet):
    """A stack"""

    def __init__(self):
        """Initialize."""
        self._stack = []

    def push(self, state):
        """Put the state in this stack."""
        self._stack.append(state)
        return True

    def pop(self):
        """Remove and return a state. Raise an IndexError if the stack is empty."""
        self._stack.pop()

    def empty(self):
        """Return whether or not this stack is empty."""
        return len(self._stack) == 0


class _Queue(_OpenSet):
    """A queue"""

    def __init__(self):
        """Initialize."""
        self._queue = deque()

    def push(self, state):
        """Put this state in this queue."""
        self._queue.append(state)
        return True

    def pop(self):
        """Remove and return a state. Raise an IndexError if the stack is empty."""
        self._queue.popleft()

    def empty(self):
        """Return whether or not this queue is empty."""
        return len(self._queue) == 0


class _PriorityQueue(_OpenSet):
    """A priority queue that uses F score"""

    def __init__(self, heuristic):
        """Initialize.

        :param heuristic: the heuristic function that maps a state to an integer
        :type heuristic: function
        """
        self._heuristic = heuristic
        self._heap = []
        self._g_score = {}
        self._last_g_score = None # g score of the last state returned from pop

    def push(self, state):
        """Put this state in this priority queue. Return whether or not it can push.

        Its parent is assumed to be the last state returned from pop.
        """
        if self._last_g_score is None:
            g_score = 0
        else:
            g_score = self._last_g_score + 1
            if g_score >= self._g_score.get(state, _INFINITY):
                return False

        self._g_score[state] = g_score
        heappush((g_score + self._heuristic(state), state))


    def pop(self):
        """Remove and return a state."""
        rtn = heappop(self._heap)[1]
        self._last_g_score = self._g_score[rtn]
        return rtn

    def empty(self):
        """Return whether or not the priority queue is empty."""
        return len(self._heap) == 0


class Problem(object):
    """Represents a problem.

    Subclass this with your own problem.
    """
    def initial_state(self):
        """Return the initial state."""
        raise NotImplementedError

    def is_goal(self, state):
        """Return whether or not this state is the goal state."""
        raise NotImplementedError

    def neighbors(self, state):
        """Return a list of states that can be reached from this state."""
        raise NotImplementedError

    def move_description(self, from_state, to_state):
        """Return a string describing the transition between the two states.

        e.g. 'Move 3H home'.
        """
        raise NotImplementedError


class NoSolutionError(Exception):
    """Represents no solution."""
    pass


def _search(problem, open_set):
    """Return a list of moves from the start node to the end node.

    :param problem: The problem
    :type problem: Problem
    :param open_set: The empty open set
    :type open_set: _OpenSet

    This may raise a NoSolutionError.
    """
    closed = set()
    came_from = {}
    open_set.push(problem.initial_state())
    while not open_set.empty():
        current = open_set.pop()
        if problem.is_goal(current):
            return _reconstruct_path(current, came_from, problem)
        closed.add(current)
        for neighbor in problem.neighbors(current):
            if neighbor in closed:
                continue
            if open_set.push(neighbor):
                came_from[neighbor] = current

    raise NoSolutionError


def astar(problem, heuristic):
    """Return a list of moves from the start node to the end node using A*.

    :param problem: The problem
    :type problem: Problem
    :param heuristic: the heuristic that takes in a state and returns an integer
    :type heuristic: function

    This may raise a NoSolutionError.
    """
    return _search(problem, _PriorityQueue(heuristic))


def dfs(problem):
    """Return a list of moves from the start node to the end node using depth first search.

    :param problem: The problem
    :type problem: Problem

    This may raise a NoSolutionError.
    """
    return _search(problem, _Stack())


def bfs(problem):
    """Return a list of moves from the start node to the end node using breadth first search.

    :param problem: The problem
    :type problem: Problem

    This may raise a NoSolutionError.
    """
    return _search(problem, _Queue())