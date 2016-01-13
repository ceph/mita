import pytest
from mock import Mock
from mita import providers
from mita.exceptions import CloudNodeNotFound


class TestOpenStackProvider(object):

    def setup(self):
        self.fake_get_driver = Mock()
        self.fake_get_driver.return_value = self.fake_get_driver

    def test_destroy_node(self):
        self.fake_get_driver.list_nodes = Mock(return_value=[])
        providers.openstack.get_driver = self.fake_get_driver
        with pytest.raises(CloudNodeNotFound):
            providers.openstack.destroy_node(name='foo')

