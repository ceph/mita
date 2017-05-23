import pytest
from collections import namedtuple
from mock import Mock
from mita import providers
from mita.exceptions import CloudNodeNotFound


class TestOpenStackProvider(object):

    def setup(self):
        self.fake_get_driver = Mock()
        self.node = namedtuple('Node', 'name')
        self.fake_get_driver.return_value = self.fake_get_driver

    def test_destroy_node(self):
        self.fake_get_driver.list_nodes = Mock(return_value=[])
        providers.openstack.get_driver = self.fake_get_driver
        with pytest.raises(CloudNodeNotFound):
            providers.openstack.destroy_node(name='foo')

    def test_destroy_node_api_fails(self):
        self.fake_get_driver.list_nodes = Mock(return_value=[self.node(name='foo')])
        # a 0 return value will mean this node was not destroyed by the API
        self.fake_get_driver.destroy_node = Mock(return_value=0)
        providers.openstack.get_driver = self.fake_get_driver
        with pytest.raises(RuntimeError):
            providers.openstack.destroy_node(name='foo')

