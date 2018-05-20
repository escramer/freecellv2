#! /usr/bin/env python

"""A Freecell solver"""

import argparse
import csv

from search import Problem, astar, dfs

_MAX_RANK = 13


class FreeCellProblem(Problem):
    """A FreeCell problem

    Description of a state:

    Each card is 2-character string.

    Each column is a string containing the concatenated cards. The last two
    characters are the playable card.

    The state is a tuple:

    0: Rank of card on home cell for suit 0
    1: Rank of card on home cell for suit 1
    2: Rank of card on home cell for suit 2
    3: Rank of card on home cell for suit 3
    4: Set of free cells
    5: Set of columns (tableau)
    """

    def __init__(self, filename):
        """Initialize from this board layout.

        :param filename: the name of the csv file
        :type filename: string
        """
        deck = self._deck()
        tableau = set()
        with open(filename) as file_obj:
            for row in csv.reader(file_obj):
                # Ignore commented rows
                if not row or not row[0] or row[0].isspace() or row[0][0] == '#':
                    continue
                column = ''
                for card in row:
                    card = card.upper()
                    deck.remove(card)
                    column += card
                tableau.add(column)

        if len(deck) > 0:
            raise ValueError('Missing cards: %s' % deck)

        self._init_state = (0, 0, 0, 0, frozenset(), frozenset(tableau))
        self._rank_map = {
            'A': 1,
            'T': 10,
            'J': 11,
            'Q': 12,
            'K': 13
        }
        self._suit_lst = ('D', 'H', 'C', 'S')
        self._suit_map = {suit_str: ndx for ndx, suit_str in enumerate(self._suit_lst)}
                
    def _deck(self):
        """Return the set of all cards."""
        rtn = set()
        ranks = ['A', 'T', 'J', 'Q', 'K']
        for num in range(2, 10):
            ranks.append(str(num))
        for suit in 'SCHD':
            for rank in ranks:
                rtn.add('%s%s' % (rank, suit))
        return rtn

    def _is_red(self, suit):
        """Return whether or not the suit is red.

        :param suit: 'C', 'D', 'H', or 'S'
        :type suit: string
        """
        return suit in ('D', 'H')

    def _rank(self, str_rank):
        """Return the rank as an integer.

        :param str_rank: the rank as a string
        :type string
        """
        rtn = self._rank_map.get(str_rank)
        return int(str_rank) if rtn is None else rtn

    def initial_state(self):
        """Return the initial state."""
        return self._init_state

    def is_goal(self, state):
        """Return whether or not this is the goal."""
        for suit in xrange(4):
            if state[suit] != _MAX_RANK:
                return False
        return True

    def neighbors(self, state):
        """Return a list of states that can be reached from this state."""
        return self._tab_to_home(state) + self._tab_to_free(state) + self._tab_to_tab(state) + \
         self._free_to_home(state) + self._free_to_tab(state) + self._home_to_tab(state) + \
         self._home_to_free(state)

    def _tab_to_home(self, state):
        """Return the list of neighbor states where a card is moved from the tableau to home."""
        return [] #TODO

    def _tab_to_free(self, state):
        """
        Return the list of neighbor states where a card is moved from the tableau to a free
        cell.
        """
        return [] #TODO

    def _tab_to_tab(self, state):
        """Return the list of neighbor states where a card is moved within the tableau."""
        return [] #TODO

    def _free_to_home(self, state):
        """
        Return the list of neighbor states where a card is moved from a
        free cell to a home cell.
        """
        return [] #TODO

    def _free_to_tab(self, state):
        """Return the list of neighbor states where a card is moved from a
        free cell to the tableau.
        """
        return [] #TODO

    def _home_to_tab(self, state):
        """Return the list of neighbor states where a card is moved from a
        home cell to the tableau.
        """
        return [] #TODO

    def _home_to_free(self, state):
        """Return the list of neighbor states where a card is moved from a
        home cell to a free cell.
        """
        return [] #TODO

    def move_description(self, from_state, to_state):
        """Return a string describing the transition between the two states.

        e.g. 'Move 3H home'.
        """
        return '' #TODO        


def main():
    """A Freecell solver"""
    parser = argparse.ArgumentParser(description=__doc__)
    help_text = """\
CSV file for a layout of a freecell game. Each row represents a Tableau column. \
Each card is 2 characters long (e.g. "3H"). You represent 10 with "T" or "t". All \
letters may be upper or lower case. For order, the card at the end of the row \
at the top of the column and can be moved. Example (you'll have more cards than this):
3h,as,4S,KD
TD,JC,2H
"""
    parser.add_argument('filename', help=help_text)
    args = parser.parse_args()

    problem = FreeCellProblem(args.filename)
    for move in dfs(problem): # Later, change to astar
        print move


if __name__ == '__main__':
    main()