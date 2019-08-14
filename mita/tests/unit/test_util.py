import requests
import pytest

from pecan import set_config
from mita import util


from mock import patch, MagicMock

BecauseNodeIsBusy = 'Waiting for next available executor on \u2018%s\u2019'
BecauseLabelIsBusy = BecauseNodeIsBusy
BecauseLabelIsOffline = u"All nodes of label \u2018%s\u2019 are offline"
BecauseNodeIsOffline = "%s is offline"
# this one is a dupe of `BecauseLabelIsOffline` in the code, but not the same
# in logic
BecauseNodeLabelIsOffline = u"There are no nodes with the label \u2018%s\u2019"

# This is another special case where it is not necessarily a reason for being stuck, but
# can get the queue stuck. In Jenkins's source it is specified as a property of a Node:
#
#     Node.LabelMissing={0} doesn\u2019t have label {1}
BecauseLabelIsMissing = u"%s doesn\u2019t have label %s"


class TestFromLabel(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'wheezy': {'labels': ['amd64', 'huge']}},
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

    def test_label_is_busy_unicode(self):
        msg = BecauseLabelIsBusy % 'huge&&amd64'
        assert util.from_label(msg) == 'wheezy'


class TestOfflineLabel(object):

    def setup(self):
        set_config(
            {'nodes': {'centos6': {'labels': ['x86_64', 'huge']}}},
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

    def test_works_with_label_expression(self):
        msg = BecauseLabelIsOffline % 'x86_64&&huge'
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


class TestLabelIsMissing(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'centos6': {'labels': ['x86_64', 'small']}},
            'jenkins': {
                'url': 'http://jenkins.example.com',
                'user': 'alfredo',
                'token': 'secret'},
        }
        set_config(self.default_conf, overwrite=True)
        self.msg = BecauseLabelIsMissing % ('node', 'x86_64&&big')

    def test_does_not_match_a_node(self):
        assert util.from_node_without_label(self.msg) is None

    def test_matches_a_node(self):
        msg = BecauseLabelIsMissing % ('centos6', 'x86_64&&small')
        assert util.from_node_without_label(msg) == 'centos6'

    def test_does_not_match_a_node_with_combined_messages(self):
        node_labels = [("%snode" % i, 'small&&ovh') for i in range(10)]
        api_message = ';'.join([BecauseLabelIsMissing % i for i in node_labels])
        assert util.from_node_without_label(api_message) is None

    def test_matches_a_node_with_combined_messages(self):
        node_labels = [("%snode" % i, 'small&&ovh') for i in range(10)]
        offline_nodes = ["%snode" % i for i in range(12,20)]
        offline_msg = ';'.join([BecauseNodeIsOffline % i for i in offline_nodes])
        node_msg = ';'.join([BecauseLabelIsMissing % i for i in node_labels])
        api_message = "%s;%s;%s" % (offline_msg, node_msg, BecauseLabelIsMissing % ('centos6', 'small&&x86_64'))
        assert util.from_node_without_label(api_message) == 'centos6'


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

    def test_unicode_does_not_barf(self, monkeypatch):
        class FakeConn(object):
            def get_node_config(self, node_name):
                    str(node_name)
                    return '<slave></slave>'

        monkeypatch.setattr('mita.util.jenkins_connection', lambda: FakeConn())
        name = u'\u2018vagrant\u2019'
        result = util.get_node_labels(name)
        assert result == []

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


stuck_reasons = [
    "Waiting for next available executor on 10.0.1.1",
    "All nodes of label awesomest are busy",
    "SuperNode is offline",
    "There are no nodes like that"
]


garbage_reasons = [
    "All is good",
    "Not waiting for a node",
    "Running test",
    "Executing on some label"
]


class TestIsStuck(object):

    @pytest.mark.parametrize('why', stuck_reasons)
    def test_is_stuck(self, why):
        assert util.is_stuck(why) is True

    @pytest.mark.parametrize('why', garbage_reasons)
    def test_is_not_stuck(self, why):
        assert util.is_stuck(why) is False


class TestFromOfflineExecutor(object):
    def setup(self):
        set_config(
            {'nodes': {'centos6': {'labels': ['x86_64']}}},
            overwrite=True
        )

    def test_none_node_does_not_break(self):
        assert util.from_offline_executor(None) is None


class TestJobFromUrl(object):

    def test_url_with_job_in_the_name(self):
        url = u'https://jenkins.ceph.com/job/jenkins-job-builder'
        result = util.job_from_url(url)
        assert result == 'jenkins-job-builder'

    def test_url_with_trailing_slash__gets_trimmed(self):
        url = u'https://jenkins.ceph.com/job/jenkins-job-builder/'
        result = util.job_from_url(url)
        assert result == 'jenkins-job-builder'

    def test_url_from_a_matrix_job(self):
        url = u'https://jenkins.ceph.com/job/ceph-dev-build/ARCH=x86_64,AVAILABLE_ARCH=x86_64,AVAILABLE_DIST=xenial,DIST=xenial,MACHINE_SIZE=huge/'
        result = util.job_from_url(url)
        assert result == "ARCH=x86_64,AVAILABLE_ARCH=x86_64,AVAILABLE_DIST=xenial,DIST=xenial,MACHINE_SIZE=huge"


class TestMatchNodeFromMatrixJobName(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'wheezy': {'labels': ['amd64', 'debian']}},
            'jenkins': {
                'url': 'http://jenkins.example.com',
                'user': 'alfredo',
                'token': 'secret'},
        }
        set_config(self.default_conf, overwrite=True)

    def test_finds_a_node(self):
        job_name = "ARCH=amd64,DIST=debian"
        result = util.match_node_from_matrix_job_name(job_name)
        assert result == "wheezy"

    def test_does_not_find_a_node(self):
        job_name = "DIST=xenial"
        result = util.match_node_from_matrix_job_name(job_name)
        assert not result

    def test_finds_node_partial_match(self):
        job_name = "DIST=debian"
        result = util.match_node_from_matrix_job_name(job_name)
        assert result == "wheezy"

    def test_duplicate_labels_in_name(self):
        job_name = "DIST=debian,AVAILABLE_DIST=debian"
        result = util.match_node_from_matrix_job_name(job_name)
        assert result == "wheezy"


class TestMatchNodeFromJobConfig(object):

    def setup(self):
        self.default_conf = {
            'nodes': {'wheezy': {'labels': ['amd64', 'debian']}},
            'jenkins': {
                'url': 'http://jenkins.example.com',
                'user': 'alfredo',
                'token': 'secret'},
        }
        set_config(self.default_conf, overwrite=True)

    @patch("mita.util.requests")
    def test_finds_labels(self, m_requests):
        mock_response = MagicMock()
        job_config = '<?xml version="1.0" encoding="UTF-8"?><project><assignedNode>amd64 &amp;&amp; debian</assignedNode></project>'
        mock_response.text = job_config
        m_requests.get.return_value = mock_response
        result = util.match_node_from_job_config("https://jenkins.ceph.com/job/ceph-pull-requests")
        assert result == "wheezy"

    @patch("mita.util.requests")
    def test_does_not_find_labels(self, m_requests):
        mock_response = MagicMock()
        job_config = '<?xml version="1.0" encoding="UTF-8"?><project></project>'
        mock_response.text = job_config
        m_requests.get.return_value = mock_response
        result = util.match_node_from_job_config("https://jenkins.ceph.com/job/ceph-pull-requests")
        assert not result

    @patch("mita.util.requests")
    def test_failed_to_fetch_job_config(self, m_requests):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException()
        m_requests.get.return_value = mock_response
        result = util.match_node_from_job_config("https://jenkins.ceph.com/job/ceph-pull-requests")
        assert not result
