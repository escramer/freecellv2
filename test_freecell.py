import pytest

from freecell import Card, FreeCellProblem

def test_card():
    """Test the Card class."""
    card = Card(1, 2)
    assert card.rank_str == 'A'
    assert card.rank_int == 1
    assert card.suit_str == 'C'
    assert card.suit_int == 2
    assert str(card) == 'AC'
    assert not card.is_red
    assert card.type == (1, False)
    assert card.next_type is None
    assert card.tup == (1, 2)

    card = Card(5, 1)
    assert card.next_type == (4, False)

class TestFreeCellProblem:

    prob = FreeCellProblem('init_state.csv')

    @staticmethod
    def _equal_no_order(lst1, lst2):
        """Return whether or not these lists are equal without regards to order."""
        return isinstance(lst1, list) and isinstance(lst2, list) and set(lst1) == set(lst2)

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

    def test_new_state(self):
        state = (3, 8, 10, 0, frozenset(['3H']), frozenset(['6C8C', '9S3C']))
        assert self.prob._new_state(state) == state

        assert self.prob._new_state(state, free=frozenset()) == \
         (3, 8, 10, 0, frozenset(), frozenset(['6C8C', '9S3C']))

    def test_av_home(self):
        state = (3, 8, 10, 0, frozenset(), frozenset())
        assert self.prob._av_home(state) == {(3, 0), (8, 1), (10, 2)}

    def test_needed_home(self):
        state = (3, 8, 13, 0, frozenset(), frozenset())
        assert self.prob._needed_home(state) == {(4, 0), (9, 1), (1, 3)}

    def test_av_tab(self):
        tab = frozenset(['3H6C', '6S'])
        assert self.prob._av_tab(tab) == {(6, 2): '3H6C', (6, 3): '6S'}

    def test_needed_tab(self):
        av_tab = {(1, 1): '4HAH', (9, 2): '4D9C', (13, 0): 'KD', (13, 1): 'KH'}
        result = self.prob._needed_tab(av_tab)
        assert isinstance(result, dict)
        assert set(result) == {(8, True), (12, False)}
        assert result[(8, True)] == ['4D9C']
        assert self._equal_no_order(result[(12, False)], ['KD', 'KH'])


