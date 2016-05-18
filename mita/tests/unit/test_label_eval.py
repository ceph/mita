import pytest
from mita.label_eval import (
    pythonize_boolean,
    validate_and_parse,
    matching_nodes
)

boolean_exprs = [
    ('a&&b', 'a and b'),
    ('a||b', 'a or b'),
    ('a&&!b', 'a and not b'),
    ('!a&&!b', 'not a and not b'),
    ('!(a||b)', 'not (a or b)'),
]

invalid_exprs = ['a.0', 'a.b', 'a.call()', '"a".len()', 'a.__dict__']


class TestPythonize(object):

    @pytest.mark.parametrize('expr,pyexpr', boolean_exprs)
    def test_valid_expr(self, expr, pyexpr):
        assert pythonize_boolean(expr) == pyexpr

    def test_valid_value(self):
        assert pythonize_boolean('a.b') == 'a.b'


class TestValidateAndParse(object):

    # all of the boolean_exprs mention only 'a' and 'b'
    @pytest.mark.parametrize('expr,pyexpr', boolean_exprs)
    def test_validate_good_exprs(self, expr, pyexpr):
        print "expr: ", expr
        expr = pythonize_boolean(expr)
        assert validate_and_parse(expr) == set(['a', 'b'])

    @pytest.mark.parametrize('expr', invalid_exprs)
    def test_validate_bad_exprs_are_caught(self, expr):
        assert validate_and_parse(expr) == set()

    def test_validate_complex_expr(self):
        expr = pythonize_boolean('((a&&b) || ((a&&!b) && (a || !c)))')
        assert validate_and_parse(expr) == set(['a', 'b', 'c'])


nodes = {
    'wheezy_huge': {'labels': ['amd64', 'wheezy', 'huge']},
    'wheezy_small': {'labels': ['amd64', 'wheezy', 'small']},
}


match_exprs = [
    ('wheezy', ['wheezy_huge', 'wheezy_small']),
    ('huge||small', ['wheezy_huge', 'wheezy_small']),
    ('huge', ['wheezy_huge']),
    ('small', ['wheezy_small']),
    ('huge&&amd64', ['wheezy_huge']),
    ('amd64&&!small', ['wheezy_huge']),
    ('arm64', []),
    ('(amd64 && trusty) || (arm64 && wheezy)', []),
]


class TestLabelMatch(object):

    @pytest.mark.parametrize('expr,matches', match_exprs)
    def test_matching_nodes(self, expr, matches):
        assert sorted(matching_nodes(expr, nodes)) == sorted(matches)
