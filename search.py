"""Depth first search, breadth first search, and A*

See https://en.wikipedia.org/wiki/A*_search_algorithm
"""

from collections import deque
from heapq import heappush, heappop
import logging
from time import time

_INFINITY = float('inf')


class _OpenSet(object):
    """An object for pushing on states and popping them off."""

    def push(self, state, cost):
        """Put this state in this open set if possible.

        This will return whether or not the state can be pushed.

        :param cost: the cost to go from the parent state to this state
        :type cost: integer
        """
        raise NotImplementedError

    def pop(self):
        """Remove and return a state. Raise an IndexError if the set is empty."""
        raise NotImplementedError

    def empty(self):
        """Return whether or not this open set is empty."""
        raise NotImplementedError

    def __len__(self):
        """Return the length of this open set."""
        raise NotImplementedError


class _Stack(_OpenSet):
    """A stack"""

    def __init__(self):
        """Initialize."""
        self._stack = []

    def push(self, state, _):
        """Put the state in this stack."""
        self._stack.append(state)
        return True

    def pop(self):
        """Remove and return a state. Raise an IndexError if the stack is empty."""
        self._stack.pop()

    def empty(self):
        """Return whether or not this stack is empty."""
        return len(self._stack) == 0

    def __len__(self):
        """Return the length."""
        return len(self._stack)


class _Queue(_OpenSet):
    """A queue"""

    def __init__(self):
        """Initialize."""
        self._queue = deque()

    def push(self, state, _):
        """Put this state in this queue."""
        self._queue.append(state)
        return True

    def pop(self):
        """Remove and return a state. Raise an IndexError if the stack is empty."""
        self._queue.popleft()

    def empty(self):
        """Return whether or not this queue is empty."""
        return len(self._queue) == 0

    def __len__(self):
        """Return the length."""
        return len(self._queue)


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

    def push(self, state, cost):
        """Put this state in this priority queue. Return whether or not it can push.

        :param cost: the cost to go from the parent state to this state
        :type cost: integer

        Its parent is assumed to be the last state returned from pop.
        """
        if self._last_g_score is None:
            g_score = 0
        else:
            g_score = self._last_g_score + cost
            if g_score >= self._g_score.get(state, _INFINITY):
                return False

        self._g_score[state] = g_score
        heappush(self._heap, (g_score + self._heuristic(state), state))
        return True


    def pop(self):
        """Remove and return a state."""
        rtn = heappop(self._heap)[1]
        self._last_g_score = self._g_score[rtn]
        return rtn

    def empty(self):
        """Return whether or not the priority queue is empty."""
        return len(self._heap) == 0

    def __len__(self):
        """Return the length."""
        return len(self._heap)


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
        """Return a list of (state, cost) tuples that can be reached from this state."""
        raise NotImplementedError

    def move_description(self, from_state, to_state):
        """Return a string describing the transition between the two states.

        e.g. 'Move 3H home'.
        """
        raise NotImplementedError


class NoSolutionError(Exception):
    """Represents no solution."""
    pass


def _reconstruct_path(current, came_from, problem):
    """Return a list of moves.

    :param current: the final state
    :type current: a state
    :param came_from: maps a state to its parent
    :type came_from: dict
    :param problem: a problem
    :type problem: Problem
    """
    rtn = []
    while current in came_from:
        parent = came_from[current]
        rtn.append(problem.move_description(parent, current))
        current = parent
    return reversed(rtn)


def _search(problem, open_set):
    """Return a list of moves from the start node to the end node.

    :param problem: The problem
    :type problem: Problem
    :param open_set: The empty open set
    :type open_set: _OpenSet

    This may raise a NoSolutionError.
    """
    logging.info('Starting search')
    closed = set()
    came_from = {}
    open_set.push(problem.initial_state(), 0)
    last_time = int(time())
    while not open_set.empty():
        new_time = int(time())
        if new_time >= last_time + 10:
            logging.info('Open set size: %s' % len(open_set))
            last_time = new_time
        current = open_set.pop()
        if problem.is_goal(current):
            logging.info('Found solution')
            return _reconstruct_path(current, came_from, problem)
        closed.add(current)
        for neighbor, cost in problem.neighbors(current):
            if neighbor in closed:
                continue
            if open_set.push(neighbor, cost):
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