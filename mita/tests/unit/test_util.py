from pecan import set_config
from mita import util

BecauseNodeIsBusy = 'Waiting for next available executor on %s'
BecauseLabelIsBusy = BecauseNodeIsBusy
BecauseLabelIsOffline = u"All nodes of label \u2018%s\u2019 are offline"
BecauseNodeIsOffline = "%s is offline"


class TestFromLabel(object):

    def setup(self):
        set_config(
            {'nodes': {'wheezy': {'labels': ['amd64']}}},
            overwrite=True
        )

    def test_string_is_garbage(self):
        assert util.from_label('') is None

    def test_string_is_wrong_does_not_match(self):
        set_config({'nodes': {}}, overwrite=True)
        assert util.from_label('this is not garbage') is None

    def test_string_is_right_but_does_not_match(self):
        msg = BecauseNodeIsBusy % 'wheezy'
        set_config({'nodes': {}}, overwrite=True)
        assert util.from_label(msg) is None

    def test_string_is_right_and_matches_node_from_name(self):
        msg = BecauseNodeIsBusy % 'wheezy'
        set_config({'nodes': {'wheezy': {'labels': []}}})
        assert util.from_label(msg) == 'wheezy'

    def test_string_is_right_and_matches_node_from_label(self):
        msg = BecauseNodeIsBusy % 'amd64'
        assert util.from_label(msg) == 'wheezy'

    def test_matches_node_with_plus_sign_from_name(self):
        msg = BecauseNodeIsBusy % 'wheezy+192.168.1.12'
        assert util.from_label(msg) == 'wheezy'

    def test_no_match_with_plus_sign_from_name(self):
        msg = BecauseNodeIsBusy % 'centos6+192.168.1.12'
        assert util.from_label(msg) is None


class TestOfflineLabel(object):

    def setup(self):
        set_config(
            {'nodes': {'centos6': {'labels': ['x86_64']}}},
            overwrite=True
        )
        self.msg = BecauseLabelIsOffline % 'amd64'

    def test_does_not_match_a_label(self):
        assert util.from_offline_label(self.msg) is None

    def test_name_exists_but_not_the_label(self):
        msg = BecauseLabelIsOffline % 'centos6'
        assert util.from_offline_label(msg) is None

    def test_matches_a_label(self):
        msg = BecauseLabelIsOffline % 'x86_64'
        assert util.from_offline_label(msg) == 'centos6'


class TestOfflineNode(object):

    def setup(self):
        set_config(
            {'nodes': {'centos6': {'labels': ['x86_64']}}},
            overwrite=True
        )
        self.msg = BecauseNodeIsOffline % 'rhel7'

    def test_does_not_match_a_node(self):
        assert util.from_offline_node(self.msg) is None

    def test_matches_a_node_with_plus_sign(self):
        msg = BecauseNodeIsOffline % 'centos6+192.168.168.90'
        assert util.from_offline_node(msg) == 'centos6'

    def test_matches_a_node(self):
        msg = BecauseNodeIsOffline % 'centos6'
        assert util.from_offline_node(msg) == 'centos6'
