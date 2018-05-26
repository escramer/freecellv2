#! /usr/bin/env python

"""A Freecell solver"""

import argparse
import csv
import logging

from search import Problem, astar, dfs

_MAX_RANK = 13
_MAX_COLS = 8
_MAX_FREE_CELLS = 4
_DECK_SIZE = 52
_SUIT_LST = ('D', 'H', 'C', 'S')
_RANK_LST = (None, 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K')


class Card:
    """Represents a card."""

    def __init__(self, rank, suit):
        """Initialize.

        :param rank: the rank
        :type rank: int
        :param suit: the suit
        :type suit: int
        """
        self.rank_str = _RANK_LST[rank]
        self.rank_int = rank
        self.suit_str = _SUIT_LST[suit]
        self.suit_int = suit
        self._str = '%s%s' % (self.rank_str, self.suit_str)
        self.is_red = self.suit_str in ('D', 'H')
        self.type = (rank, self.is_red)
        self.next_type = (rank - 1, not self.is_red) if rank > 1 else None # Next card type in tableau
        self.tup = (rank, suit)

    def __str__(self):
        return self._str


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
        self._cards = self._deck() # Use this to get precomputed Card objects.
        deck = set(str(card) for card in self._cards.itervalues())

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

    @staticmethod
    def _deck():
        """Return a deck of cards.

        More specifically, return a dictionary mapping a string (such as '3H')
        and its corresponding (rank, suit) tuple (for '3H', this is (3, 1))
        to its Card.
        """
        rtn = {}
        for suit_ndx, suit_str in enumerate(_SUIT_LST):
            for rank_ndx, rank_str in enumerate(_RANK_LST[1:], start=1):
                card = Card(rank_ndx, suit_ndx)
                rtn[str(card)] = card
                rtn[card.tup] = card
        return rtn

    def initial_state(self):
        """Return the initial state."""
        return self._init_state

    def is_goal(self, state):
        """Return whether or not this is the goal."""
        for suit in xrange(4):
            if state[suit] != _MAX_RANK:
                return False
        return True

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
        :type card: Card

        This returns the modified tableau. 
        i.e.
            If tableau is a frozenset, this will return a new set.
            If tableau is a set, this will return it.
        """
        if isinstance(tableau, frozenset):
            tableau = set(tableau)
        tableau.remove(col)
        col += str(card)
        tableau.add(col)
        return tableau

    @staticmethod
    def _add_card_to_new_col(tableau, card):
        """Put this card in a new column.

        :param tableau: the set of columns
        :type tableau: frozenset or set
        :param card: a card
        :type card: Card

        This returns the modified tableau. 
        i.e.
            If tableau is a frozenset, this will return a new set.
            If tableau is a set, this will return it.
        """
        if isinstance(tableau, frozenset):
            tableau = set(tableau)
        tableau.add(str(card))
        return tableau

    @staticmethod
    def _add_card_to_free(freecells, card):
        """Add this card to a free cell.

        :param freecells: the free cells (set of strings)
        :type freecells: frozenset
        :param card: a card
        :type card: Card

        This returns freecells as a new frozenset.
        """
        freecells = set(freecells)
        freecells.add(str(card))
        return frozenset(freecells)

    @staticmethod
    def _remove_card_from_free(freecells, card):
        """Remove this card from the free cells.

        :param freecells: the free cells (set of strings)
        :type freecells: frozenset
        :param card: a card
        :type card: Card

        This returns freecells as a new frozenset.
        """
        freecells = set(freecells)
        freecells.remove(str(card))
        return frozenset(freecells)

    @staticmethod
    def _to_home(state, needed_home, card):
        """Return a tuple of the 4 home cells as a result of adding this card to home.
        If the card cannot be added, return None.

        :param needed_home: a set of Cards needed
        :type needed_home: set
        :param card: a card
        :type card: Card
        """
        if card in needed_home:
            rtn = list(state[:4])
            rtn[card.suit_int] = card.rank_int
            return tuple(rtn)
        else:
            return None

    @staticmethod
    def _remove_from_home(state, card):
        """Return a tuple of the 4 home cells as a result of removing this card.

        :param card: a card
        :type card: Card
        """
        home = list(state[:4])
        home[card.suit_int] -= 1
        return tuple(home)

    def _to_tab(self, tab, needed_tab, card):
        """Return a list of tableaus resulting from putting this card in the tableau
        from outside the tableau.

        :param tab: a tableau
        :type tab: frozenset
        :param needed_tab: maps a (rank, is_red) tuple (card that's needed) to a list of columns
        :type needed_tab: dict
        :param card: a card
        :type card: Card

        The new tableaus will be frozensets.
        """
        rtn = []
        if len(tab) < _MAX_COLS:
            rtn.append(frozenset(self._add_card_to_new_col(tab, card)))
        for col in needed_tab.get(card.type, []):
            rtn.append(frozenset(self._add_card_to_col(tab, col, card)))
        return rtn

    def _within_tab(self, tab, needed_tab, av_tab):
        """Return a list of tableaus resulting from moving a card within the tableau.

        :param tab: a tableau
        :type tab: frozenset
        :param needed_tab: maps a (rank, is_red) tuple (card that's needed) to a list of columns
        :type needed_tab: dict
        :param av_tab: maps a Card to its column
        :type av_tab: dict

        The new tableaus will be frozensets.
        """
        rtn = []
        for av_card, from_col in av_tab.iteritems():
            if len(from_col) > 2 and len(tab) < _MAX_COLS:
                new_tab = self._remove_card_from_col(tab, from_col)
                new_tab = self._add_card_to_new_col(new_tab, av_card)
                rtn.append(frozenset(new_tab))
            for to_col in needed_tab.get(av_card.type, []):
                new_tab = self._remove_card_from_col(tab, from_col)
                new_tab = self._add_card_to_col(new_tab, to_col, av_card)
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

    def _av_home(self, state):
        """Return the set of available home cells."""
        rtn = set()
        for suit_ndx in xrange(4):
            rank = state[suit_ndx]
            if rank > 0:
                rtn.add(self._cards[(rank, suit_ndx)])
        return rtn

    def _needed_home(self, state):
        """Return the set of needed cards to go home."""
        rtn = set()
        for suit in xrange(4):
            rank = state[suit]
            if rank < _MAX_RANK:
                rtn.add(self._cards[(rank+1, suit)])
        return rtn

    def _av_tab(self, tab):
        """Return the available cards in the tableau.

        :param tab: the tableau
        :type tab: frozenset

        More specifically, this returns a dictionary mapping a Card to its column.
        """
        return {self._cards[col[-2:]]: col for col in tab}

    def _needed_tab(self, av_tab):
        """Return the cards that are needed in the tableau.

        :param av_tab: the available cards in the tableau (from self._av_tab)
        :type av_tab: dict

        More specifically, return a dictionary mapping a (rank, is_red) tuple to a list of columns.
        """
        rtn = {}
        for card, col in av_tab.iteritems():
            if card.rank_int > 1:
                needed = card.type
                if needed in rtn:
                    rtn[needed].append(col)
                else:
                    rtn[needed] = [col]
        return rtn

    def neighbors(self, state):
        """Return a list of states that can be reached from this state."""
        av_home = self._av_home(state)
        needed_home = self._needed_home(state)

        # Free cells
        free = {self._cards[card] for card in state[4]}

        av_tab = self._av_tab(state[5])
        needed_tab = self._needed_tab(av_tab)

        rtn = []

        ### From free
        for card in free:
            new_free = None
            # To tab
            new_tabs = self._to_tab(state[5], needed_tab, card)
            if new_tabs:
                new_free = self._remove_card_from_free(state[4], card)
                for new_tab in new_tabs:
                    rtn.append(self._new_state(state, free=new_free, tab=new_tab))

            # To home
            new_home = self._to_home(state, needed_home, card)
            if new_home is not None:
                if new_free is None:
                    new_free = self._remove_card_from_free(state[4], card)
                rtn.append(self._new_state(state, home=new_home, free=new_free))

        ### From tab
        # To tab
        for new_tab in self._within_tab(state[5], needed_tab, av_tab):
            rtn.append(self._new_state(state, tab=new_tab))
        # To free
        if len(state[4]) < _MAX_FREE_CELLS:
            for card, col in av_tab.iteritems():
                new_free = self._add_card_to_free(state[4], card)
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
                new_free = self._add_card_to_free(state[4], card)
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
        ## Check free cells
        added_free_cells = to_state[4] - from_state[4]
        if added_free_cells:
            for card in added_free_cells:
                return 'Move %s to a free cell.' % card

        ## Check home cells
        for ndx in xrange(4):
            if to_state[ndx] > from_state[ndx]:
                return 'Move %s to its home cell.' % self._cards[(to_state[ndx], ndx)]

        ## Check tableau
        to_tab = to_state[5]
        from_tab =  from_state[5]
        # Check for a card added to an existing column
        for to_col in to_tab:
            if to_col[:-2] in from_tab:
                return 'Move %s on top of %s.' % (to_col[-2:], to_col[-4:-2])
        # Check for a card added to a new column
        for to_col in to_tab:
            if len(to_col) == 2 and to_col not in from_tab:
                return 'Move %s to a new column.' % to_col

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
    # Imagine you have an infinite number of free cells.
    #
    # The idea is this:
    #  For a card c in the tableau, it must go to a free cell if there is a card with
    #  the same suit deeper in the column with a lower rank.
    rtn = len(state[4])
    for col in state[5]:
        min_cards = {suit: _MAX_RANK for suit in ['S', 'C', 'D', 'H']}
        for ndx in xrange(0, len(col), 2):
            rank = Card.int_rank(col[ndx])
            suit = col[ndx+1]
            if min_cards[suit] < rank:
                rtn += 2
            else:
                rtn += 1
                min_cards[suit] = rank
    return rtn


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

    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')
    logging.info('Starting')
    problem = FreeCellProblem(args.filename)
    for move in astar(problem, heuristic):
        print move


if __name__ == '__main__':
    main()