import pytest

from freecell import Card, FreeCellProblem

class TestCard:
    """Test the Card class."""

    def test_is_red(self):
        assert Card.is_red('D')
        assert not Card.is_red('S')
        
    def test_int_rank(self):
        assert Card.int_rank('A') == 1
        assert Card.int_rank('K') == 13

    def test_str_rank(self):
        assert Card.str_rank(1) == 'A'
        assert Card.str_rank(13) == 'K'

    def test_deck(self):
        assert Card.deck() == set(['3S', '2C', '5S', 'TS', '3C', '3H', 'JH', '5H', 'JD', '5D', '5C', '3D', '9H', '7D', '7C', '9C', '9D', 'QS', '7H', '7S', 'TH', 'TD', 'JC', 'TC', 'AC', 'AD', '2S', 'AH', '4S', '2D', 'AS', '4H', '8S', '4D', 'JS', '2H', '9S', 'KC', '8H', '6C', '6D', 'KD', '6H', '8C', '4C', 'KH', '8D', 'KS', 'QC', '6S', 'QD', 'QH'])

class TestFreeCellProblem:

    prob = FreeCellProblem('init_state.csv')

    def test_init(self):
        """Test the __init__ method."""
        assert self.prob.initial_state() == (0, 0, 0, 0, frozenset([]), frozenset(['5S7D5DJHQC4H', '2H9SJS6HKSTCTS', 'KC5H2DAC8HQD9D', '2SAH2CQS4C7S', '4S8D3HTDTH8C3S', 'JC5CKHQH9H6C7H', 'ADKD8S6D6SAS', '3D4D3C7C9CJD']))

        with pytest.raises(ValueError):
            FreeCellProblem('bad_state.csv')

    def test_is_red(self):
        assert self.prob._is_red('H')
        assert self.prob._is_red(0)

    def test_card_tup(self):
        assert self.prob._card_tup('3C') == (3, 2)

    def test_card_str(self):
        assert self.prob._card_str((3, 2)) == '3C'

    def test_is_goal(self):
        state = (13, 13, 13, 13, frozenset(), frozenset())
        assert self.prob.is_goal(state)
        state = (13, 13, 13, 12, frozenset(), frozenset())
        assert not self.prob.is_goal(state)

    def test_meeets_need(self):
        assert self.prob._meets_need((3, 2), (3, False))
        assert not self.prob._meets_need((3, 2), (4, False))

    def test_remove_card_from_col(self):
        tab = frozenset(['3H6C', '4DKD'])
        assert self.prob._remove_card_from_col(tab, '4DKD') == {'3H6C', '4D'}
        tab = frozenset(['3H6C', '4D'])
        assert self.prob._remove_card_from_col(tab, '4D') == {'3H6C'}

    def test_add_card_to_col(self):
        tab = frozenset(['3H6C', '4DKD'])
        assert self.prob._add_card_to_col(tab, '3H6C', '8S') == {'3H6C8S', '4DKD'}

    def test_add_card_to_new_col(self):
        tab = frozenset(['3H6C'])
        assert self.prob._add_card_to_new_col(tab, '8S') == {'3H6C', '8S'}

    def test_add_card_to_free(self):
        assert self.prob._add_card_to_free(frozenset(['8S']), '3D') == frozenset(['8S', '3D'])

    def test_remove_card_from_free(self):
        assert self.prob._remove_card_from_free(frozenset(['8S', '3D']), '3D') == frozenset(['8S'])

    def test_to_home(self):
        needed_home = {(3, 2)}
        state = (13, 13, 2, 13, frozenset(), frozenset())
        assert self.prob._to_home(state, needed_home, (3, 2)) == (13, 13, 3, 13)
        assert self.prob._to_home(state, needed_home, (4, 2)) is None

    def test_remove_from_home(self):
        state = (4, 8, 9, 0, frozenset(), frozenset())
        assert self.prob._remove_from_home(state, (8, 1)) == (4, 7, 9, 0)

    def test_to_tab(self):
        tab = frozenset(['3H6C', '6S', 'TD'])
        needed_tab = {
            (5, True): ['3H6C', '6S'],
            (9, False): ['TD']
        }
        result = self.prob._to_tab(tab, needed_tab, (5, 1))
        assert isinstance(result, list) and set(result) == {
            frozenset(['3H6C5H', '6S', 'TD']),
            frozenset(['3H6C', '6S5H', 'TD']),
            frozenset(['3H6C', '6S', 'TD', '5H'])
        }


        tab = frozenset(['3H', 'AC', '7C', 'JD', '9S', '9D', 'KH', '7S'])
        needed_tab = {
            (2, False): ['3H'],
            (6, True): ['7C', '7S'],
            (10, False): ['JD'],
            (8, True): ['9S'],
            (8, False): ['9D'],
            (12, False): ['KH']
        }
        assert self.prob._to_tab(tab, needed_tab, (2, 0)) == []

    def test_card_type(self):
        assert self.prob._card_type((5, 2)) == (5, False)

    def test_within_tab(self):
        tab = frozenset(['3H6C', '6S'])
        av_tab = self.prob._av_tab(tab)
        needed_tab = self.prob._needed_tab(av_tab)
        assert self.prob._within_tab(tab, needed_tab, av_tab) == [frozenset(['3H', '6S', '6C'])]

        tab = frozenset(['AC', 'AS', 'AD', 'AH', '3C', '3S', '3D', '3H'])
        av_tab = self.prob._av_tab(tab)
        needed_tab = self.prob._needed_tab(av_tab)
        assert self.prob._within_tab(tab, needed_tab, av_tab) == []

        tab = frozenset(['AC', 'AS', 'AD', 'AH', '3H6C', '7H', 'KD8C', 'JDTD'])
        av_tab = self.prob._av_tab(tab)
        needed_tab = self.prob._needed_tab(av_tab)
        result = self.prob._within_tab(tab, needed_tab, av_tab)
        assert isinstance(result, list) and set(result) == {
            frozenset(['AC', 'AS', 'AD', 'AH', '3H', '7H6C', 'KD8C', 'JDTD']),
            frozenset(['AC', 'AS', 'AD', 'AH', '3H6C', 'KD8C7H', 'JDTD'])
        }


