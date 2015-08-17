from mock import Mock


class TestNodesController(object):

    def test_create_new_node(self, session, monkeypatch):
        monkeypatch.setattr('mita.providers.openstack.create_node', Mock())
        result = session.app.post_json(
            '/api/nodes/',
            params={
                'name': 'wheezy',
                'provider': 'openstack',
                'keyname': 'ci-key',
                'image_name': 'beefy-wheezy',
                'size': '3xlarge',
                'labels': ['wheezy', 'debian'],
            }
        )
        assert result.status_int == 200
