from pecan import set_config
from mita import util

BecauseNodeIsBusy = 'Waiting for next available executor on %s'
BecauseLabelIsBusy = BecauseNodeIsBusy
BecauseLabelIsOffline = u"All nodes of label \u2018%s\u2019 are offline"
BecauseNodeIsOffline = "%s is offline"
# this one is a dupe of `BecauseLabelIsOffline` in the code, but not the same
# in logic
BecauseNodeLabelIsOffline = u"There are no nodes with the label \u2018%s\u2019"


class TestFromLabel(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'wheezy': {'labels': ['amd64']}},
            'jenkins': {
                'url': 'http://jenkins.example.com',
                'user': 'alfredo',
                'token': 'secret'},
        }
        set_config(self.default_conf, overwrite=True)

    def test_string_is_garbage(self):
        assert util.from_label('') is None

    def test_string_is_wrong_does_not_match(self):
        self.default_conf['nodes'] = {}
        set_config(self.default_conf, overwrite=True)
        assert util.from_label('this is not garbage') is None

    def test_string_is_right_but_does_not_match(self):
        msg = BecauseNodeIsBusy % 'wheezy'
        self.default_conf['nodes'] = {}
        set_config(self.default_conf, overwrite=True)
        assert util.from_label(msg) is None

    def test_string_is_right_and_matches_node_from_name(self):
        msg = BecauseNodeIsBusy % 'wheezy'
        self.default_conf['nodes']['wheezy']['labels'] = []
        set_config(self.default_conf, overwrite=True)
        assert util.from_label(msg) == 'wheezy'

    def test_string_is_right_and_matches_node_from_label(self):
        msg = BecauseNodeIsBusy % 'amd64'
        assert util.from_label(msg) == 'wheezy'

    def test_matches_node_with_plus_sign_from_name(self):
        msg = BecauseNodeIsBusy % 'wheezy__192.168.1.12'
        assert util.from_label(msg) == 'wheezy'

    def test_no_match_with_plus_sign_from_name(self):
        msg = BecauseNodeIsBusy % 'centos6__192.168.1.12'
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
        msg = BecauseNodeIsOffline % 'centos6__192.168.168.90'
        assert util.from_offline_node(msg) == 'centos6'

    def test_matches_a_node(self):
        msg = BecauseNodeIsOffline % 'centos6'
        assert util.from_offline_node(msg) == 'centos6'

    def test_matches_a_fallback(self):
        msg = BecauseNodeIsOffline % '10.0.0.0_centos6_huge'
        assert util.from_offline_node(msg) == 'centos6'


class TestFromOfflineNodeLabel(object):

    def setup(self):
        set_config(
            {'nodes': {'centos': {'labels': ['x86_64', 'centos', 'centos6']}}},
            overwrite=True
        )

    def test_multiple_label_does_not_match(self):
        msg = BecauseNodeLabelIsOffline % "x86_64&&rhel"
        assert util.from_offline_node_label(msg) is None

    def test_single_label_does_not_match(self):
        msg = BecauseNodeLabelIsOffline % "rhel"
        assert util.from_offline_node_label(msg) is None

    def test_multiple_label_matches(self):
        msg = BecauseNodeLabelIsOffline % "x86_64&&centos"
        assert util.from_offline_node_label(msg) == 'centos'

    def test_three_labels_matches(self):
        msg = BecauseNodeLabelIsOffline % "x86_64&&centos&&centos6"
        assert util.from_offline_node_label(msg) == 'centos'

    def test_single_label_matches(self):
        msg = BecauseNodeLabelIsOffline % "x86_64"
        assert util.from_offline_node_label(msg) == 'centos'


class TestMatchNode(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'wheezy': {'labels': ['amd64', 'debian']}},
            'jenkins': {
                'url': 'http://jenkins.example.com',
                'user': 'alfredo',
                'token': 'secret'},
        }
        set_config(self.default_conf, overwrite=True)

    def test_busy_node(self):
        result = util.match_node(BecauseNodeIsBusy % 'wheezy')
        assert result == 'wheezy'

    def test_busy_node_no_match(self):
        result = util.match_node(BecauseNodeIsBusy % 'solaris')
        assert result is None

    def test_busy_label(self):
        result = util.match_node(BecauseLabelIsBusy % 'amd64')
        assert result == 'wheezy'

    def test_busy_label_no_match(self):
        result = util.match_node(BecauseLabelIsBusy % 'x86_64')
        assert result is None

    def test_single_nodelabel_is_offline(self):
        result = util.match_node(BecauseNodeLabelIsOffline % 'debian')
        assert result == 'wheezy'

    def test_multi_nodelabel_is_offline(self):
        result = util.match_node(BecauseNodeLabelIsOffline % 'debian&&amd64')
        assert result == 'wheezy'

    def test_multi_nodelabel_is_offline_no_match(self):
        result = util.match_node(BecauseNodeLabelIsOffline % 'fast&&debian&&amd64')
        assert result is None


class TestGetNodeLabels(object):

    def setup(self):
        util.jenkins_connection = lambda: None

    def test_get_no_node_labels(self):
        result = util.get_node_labels('trusty', _xml_configuration='<slave></slave>')
        assert result == []

    def test_get_correct_node_labels(self):
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
<slave>
  <name>centos7+158.69.77.220</name>
  <description></description>
  <remoteFS>/home/jenkins-build/build</remoteFS>
  <numExecutors>1</numExecutors>
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$Always"/>
  <launcher class="hudson.plugins.sshslaves.SSHLauncher" plugin="ssh-slaves@1.10">
    <host>158.69.77.220</host>
    <port>22</port>
    <credentialsId>39fa150b-b2a1-416e-b334-29a9a2c0b32d</credentialsId>
    <maxNumRetries>0</maxNumRetries>
    <retryWaitTime>0</retryWaitTime>
  </launcher>
  <label>amd64 centos7 x86_64 huge</label>
  <nodeProperties/>
  <userId>prado</userId>
</slave>
        """
        result = util.get_node_labels('trusty', _xml_configuration=xml_string)
        assert result == ['amd64', 'centos7', 'x86_64', 'huge']

