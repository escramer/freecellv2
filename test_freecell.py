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

    def test_init(self):
        """Test the __init__ method."""
        prob = FreeCellProblem('init_state.csv')
        assert prob.initial_state() == (0, 0, 0, 0, frozenset([]), frozenset(['5S7D5DJHQC4H', '2H9SJS6HKSTCTS', 'KC5H2DAC8HQD9D', '2SAH2CQS4C7S', '4S8D3HTDTH8C3S', 'JC5CKHQH9H6C7H', 'ADKD8S6D6SAS', '3D4D3C7C9CJD']))

        with pytest.raises(ValueError):
            FreeCellProblem('bad_state.csv')
            