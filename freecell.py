#! /usr/bin/env python

"""A Freecell solver"""

import argparse
import csv

from search import Problem, astar, dfs

_MAX_RANK = 13
_MAX_COLS = 8
_MAX_FREE_CELLS = 4
_DECK_SIZE = 52


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
        self._rank_lst = (None, 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K')
        self._suit_lst = ('D', 'H', 'C', 'S')
        self._suit_map = {suit_str: ndx for ndx, suit_str in enumerate(self._suit_lst)}
        self._red_suits = tuple(self._is_red(suit) for suit in self._suit_lst)
                
    @staticmethod
    def _deck():
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

        :param suit: the suit
        :type suit: string or int
        """
        return suit in ('D', 'H') if isinstance(suit, str) else self._red_suits[suit]

    def _int_rank(self, str_rank):
        """Return the rank as an integer.

        :param str_rank: the rank as a string
        :type string
        """
        rtn = self._rank_map.get(str_rank)
        return int(str_rank) if rtn is None else rtn

    def _card_tup(self, card_str):
        """Return a (rank, suit) tuple (both integers) representing this card.

        :param card_str: a card
        :type card_str: string
        """
        return (self._int_rank(card_str[0]), self._suit_map[card_str[1]])

    def _card_str(self, card_tup):
        """Return the card as a string.

        :param card_tup: a (rank, suit) tuple (both integers)
        :type card_tup: tuple
        """
        return '%s%s' % (self._rank_lst[card_tup[0]], self._suit_lst[card_tup[1]])

    def initial_state(self):
        """Return the initial state."""
        return self._init_state

    def is_goal(self, state):
        """Return whether or not this is the goal."""
        for suit in xrange(4):
            if state[suit] != _MAX_RANK:
                return False
        return True

    def _meets_need(self, card, need):
        """Return whether or not this card has the matching rank and suit.

        :param card: a (rank, suit) tuple (both integers)
        :type card: tuple
        :param need: a (rank, is_red) tuple
        :type need: tuple
        """
        return card[0] == need[0] and self._is_red(card[1]) == need[1]

    @staticmethod
    def _remove_card_from_col(tableau, col):
        """Remove a card from the column.

        :param tableau: the set of columns
        :type tableau: frozenset or set
        :param col: the column
        :type col: string

        This returns the modified tableau. 
        i.e.
            If tableau is a frozenset, this will return a new set.
            If tableau is a set, this will return it.
        """
        if isinstance(tableau, frozenset):
            tableau = set(tableau)
        tableau.remove(col)
        col = col[:-2]
        if col:
            tableau.add(col)
        return tableau

    @staticmethod
    def _add_card_to_col(tableau, col, card):
        """Add a card to a column.

        :param tableau: the set of columns
        :type tableau: set or frozenset
        :param col: a column
        :type col: string
        :param card: a card
        :type card: string

        This returns the modified tableau. 
        i.e.
            If tableau is a frozenset, this will return a new set.
            If tableau is a set, this will return it.
        """
        if isinstance(tableau, frozenset):
            tableau = set(tableau)
        tableau.remove(col)
        col += card
        tableau.add(col)
        return tableau

    @staticmethod
    def _add_card_to_new_col(tableau, card):
        """Put this card in a new column.

        :param tableau: the set of columns
        :type tableau: frozenset or set
        :param card: a card
        :type card: string

        This returns the modified tableau. 
        i.e.
            If tableau is a frozenset, this will return a new set.
            If tableau is a set, this will return it.
        """
        if isinstance(tableau, frozenset):
            tableau = set(tableau)
        tableau.add(card)
        return tableau

    @staticmethod
    def _add_card_to_free(freecells, card):
        """Add this card to a free cell.

        :param freecells: the free cells
        :type freecells: frozenset
        :param card: a card
        :type card: string

        This returns freecells as a new frozenset.
        """
        freecells = set(freecells)
        freecells.add(card)
        return frozenset(freecells)

    @staticmethod
    def _remove_card_from_free(freecells, card):
        """Remove this card from the free cells.

        :param freecells: the free cells
        :type freecells: frozenset
        :param card: a card
        :type card: string

        This returns freecells as a new frozenset.
        """
        freecells = set(freecells)
        freecells.remove(card)
        return frozenset(freecells)

    @staticmethod
    def _to_home(state, needed_home, card):
        """Return a tuple of the 4 home cells as a result of adding this card to home.
        If the card cannot be added, return None.

        :param needed_home: a set of cards needed (each card is a (rank, suit) tuple)
        :type needed_home: set
        :param card: a (rank, suit) tuple (both integers)
        :type card: tuple
        """
        if card in needed_home:
            home = list(state[:4])
            home[card[1]] = card[0]
            return tuple(home)
        else:
            return None

    @staticmethod
    def _remove_from_home(state, card):
        """Return a tuple of the 4 home cells as a result of removing this card.

        :param card: a (rank, suit) tuple (both integers)
        :type card: tuple
        """
        home = list(state[:4])
        home[card[1]] -= 1
        return tuple(home)

    def _to_tab(self, tab, needed_tab, card):
        """Return a list of tableaus resulting from putting this card in the tableau
        from outside the tableau.

        :param tab: a tableau
        :type tab: frozenset
        :param needed_tab: maps a (rank, is_red) tuple (card that's needed) to its column
        :type needed_tab: dict
        :param card: a (rank, suit) tuple
        :type card: tuple

        The new tableaus will be frozensets.
        """
        rtn = []
        card_str = self._card_str(card)
        if len(tab) < _MAX_COLS:
            rtn.append(frozenset(self._add_card_to_new_col(tab, card_str)))
        for need, col in needed_tab.iteritems():
            if self._meets_need(card, need):
                rtn.append(frozenset(self._add_card_to_col(tab, col, card_str)))
        return rtn

    def _within_tab(self, tab, needed_tab, av_tab):
        """Return a list of tableaus resulting from moving a card within the tableau.

        :param tab: a tableau
        :type tab: frozenset
        :param needed_tab: maps a (rank, is_red) tuple (card that's needed) to its column
        :type needed_tab: dict
        :param av_tab: maps available (rank, suit) tuples to their column
        :type av_tab: dict

        The new tableaus will be frozensets.
        """
        rtn = []
        for av_card, from_col in av_tab.iteritems():
            av_card_str = self._card_str(av_card)
            if len(from_col) > 2 and len(tab) < _MAX_COLS:
                new_tab = self._remove_card_from_col(tab, from_col)
                new_tab = self._add_card_to_new_col(new_tab, av_card_str)
                rtn.append(frozenset(new_tab))
            for need, to_col in needed_tab.iteritems():
                if self._meets_need(av_card, need):
                    new_tab = self._remove_card_from_col(tab, from_col)
                    new_tab = self._add_card_to_col(new_tab, to_col, av_card_str)
                    rtn.append(frozenset(new_tab))
        return rtn

    @staticmethod
    def _new_state(state, home=None, free=None, tab=None):
        """Return a new state with some modifications.

        If any of the options are not None, they will appear in the new state. Otherwise,
        whatever's in "state" will appear in the new state.
        
        :param home: the home cells
        :type home: tuple
        :param free: the free cells
        :type free: frozenset
        :param tab: the tableau
        :type tab: frozenset
        """
        if home is None:
            home = state[:4]
        if free is None:
            free = state[4]
        if tab is None:
            tab = state[5]
        return home + (free, tab)

    def neighbors(self, state):
        """Return a list of states that can be reached from this state."""
        # Available home cells
        av_home = set()
        for suit_ndx in xrange(4):
            rank = state[suit_ndx]
            if rank > 0:
                av_home.add((rank, suit_ndx))

        # Needed home_cells
        needed_home = {(rank+1, suit) for rank, suit in av_home if rank < _MAX_RANK}

        # Free cells
        free = {self._card_tup(card) for card in state[4]}

        # Available and needed tableau cards
        av_tab = {} # Maps a card to its pile
        needed_tab = {} # Maps a needed (rank, is_red) tuple to its pile
        for col in state[5]:
            av_card = self._card_tup(col[-2:])
            av_tab[av_card] = col
            if av_card[0] > 1:
                needed_tab[(av_card[0] - 1, av_card[1])] = col

        rtn = []

        ### From free
        for card in free:
            new_free = None
            # To tab
            new_tabs = self._to_tab(state[5], needed_tab, card)
            if new_tabs:
                card_str = self._card_str(card)
                new_free = self._remove_card_from_free(state[4], card_str)
                for new_tab in new_tabs:
                    rtn.append(self._new_state(state, free=new_free, tab=new_tab))

            # To home
            new_home = self._to_home(state, needed_home, card)
            if new_home is not None:
                if new_free is None:
                    new_free = self._remove_card_from_free(state[4], card_str)
                rtn.append(self._new_state(state, home=new_home, free=new_free))

        ### From tab
        # To tab
        for new_tab in self._within_tab(state[5], needed_tab, av_tab):
            rtn.append(self._new_state(state, tab=new_tab))
        # To free
        if len(state[4]) < _MAX_FREE_CELLS:
            for card, col in av_tab.iteritems():
                card_str = self._card_str(card)
                new_free = self._add_card_to_free(state[4], card_str)
                new_tab = frozenset(self._remove_card_from_col(state[5], col))
                rtn.append(self._new_state(state, free=new_free, tab=new_tab))
        # To home
        for card, col in av_tab.iteritems():
            new_home = self._to_home(state, needed_home, card)
            if new_home is not None:
                new_tab = frozenset(self._remove_card_from_col(state[5], col))
                rtn.append(self._new_state(state, home=new_home, tab=new_tab))

        ### From home
        for card in av_home:
            new_home = None
            # To free
            if len(state[4]) < _MAX_FREE_CELLS:
                card_str = self._card_str(card)
                new_free = self._add_card_to_free(state[4], card_str)
                new_home = self._remove_from_home(state, card)
                rtn.append(self._new_state(state, home=new_home, free=new_free))
            # To tab
            for new_tab in self._to_tab(state[5], needed_tab, card):
                new_home = self._remove_from_home(state, card) if new_home is None else new_home
                rtn.append(self._new_state(state, home=new_home, tab=new_tab))

        return rtn

    def move_description(self, from_state, to_state):
        """Return a string describing the transition between the two states.

        e.g. 'Move 3H home'.
        """
        # Check free cells
        added_free_cells = to_state[4] - from_state[4]
        if added_free_cells:
            for card in added_free_cells:
                return 'Move %s to a free cell.' % card

        # Check home cells
        for ndx in xrange(4):
            if to_state[ndx] > from_state[ndx]:
                card_str = self._card_str((to_state[ndx], ndx))
                return 'Move %s to its home cell.' % card_str

        # Check tableau
        to_tab = to_state[5]
        from_tab =  from_state[5]
        if len(to_tab) == len(from_tab):
            for from_col in from_tab:
                for to_col in to_tab:
                    if to_col.startswith(from_col):
                        return 'Move %s on top of %s.' % (to_col[-2:], to_col[-4:-2])
        else:
            for from_col in from_tab:
                for to_col in to_tab:
                    if from_col.startswith(to_col):
                        return 'Move %s to a new column.' % from_col[-2:]

        raise ValueError('Unable to find the right move')

    def display(self, state):
        """Display this state in a nice way."""
        # First row
        gap = 4 # Number of spaces between free and home cells
        row = '|'
        for card in sorted(state[4]):
            row += card + '|'
        for _ in range(4 - len(state[4])):
            row += '  |'
        row += ' ' * gap + '|'
        for ndx in xrange(4):
            home_rank = state[ndx]
            if home_rank == 0:
                row += '  '
            else:
                row += self._card_str((home_rank, ndx))
            row += '|'
        print row

        # Second row
        print '+--+--+--+--+' + '-' * gap + '+--+--+--+--+'

        # Tableau
        max_len = max(len(col) for col in state[5]) / 2
        for ndx in xrange(max_len):
            row = ''
            for col in sorted(state[5]):
                if ndx * 2 < len(col):
                    card = col[ndx*2:ndx*2+2]
                else:
                    card = '  '
                row += card + '  '
            print row


def heuristic(state):
    """Return the heuristic."""
    return _DECK_SIZE - sum(state[:4])


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
    for move in astar(problem, hearistic):
        print move


if __name__ == '__main__':
    main()