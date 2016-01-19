from mita import expressions


class TestGroups(object):

    def test_only_ands(self):
        expression = "(foo && bar) && (baz && meh)"
        result = expressions.expand(expression)
        assert result == [['foo', 'bar', 'baz', 'meh']]

    def test_only_ors(self):
        expression = "(foo || bar) || (baz || meh)"
        result = expressions.expand(expression)
        assert result == [
            ['foo', 'baz'],
            ['foo', 'meh'],
            ['bar', 'baz'],
            ['bar', 'meh']
        ]


class TestPlain(object):

    def test_ands_only(self):
        expression = "foo&&bar&&baz"
        result = expressions.expand(expression)
        assert result == [['foo', 'bar', 'baz']]

    def test_ors_only(self):
        expression = "foo||baz||bar"
        result = expressions.expand(expression)
        assert result == [['foo'], ['baz'], ['bar']]


class TestRealUsage(object):

    def test_make_check_labels(self):
        expression = "huge&&(trusty||centos)"
        result = expressions.expand(expression)
        assert result == [['huge', 'trusty'], ['huge', 'centos']]
