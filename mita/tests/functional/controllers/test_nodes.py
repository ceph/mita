from mock import Mock
from mita.models import Node


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
                'script': '#!/bin/bash echo hello world!',
                'labels': ['wheezy', 'debian'],
            }
        )
        assert result.status_int == 200

    def test_idle_is_unset(self, session, monkeypatch):
        monkeypatch.setattr('mita.providers.openstack.create_node', Mock())
        session.app.post_json(
            '/api/nodes/',
            params={
                'name': 'wheezy',
                'provider': 'openstack',
                'keyname': 'ci-key',
                'image_name': 'beefy-wheezy',
                'size': '3xlarge',
                'script': '#!/bin/bash echo hello world! %s',
                'labels': ['wheezy', 'amd64'],
            }
        )
        node = Node.get(1)
        assert node.idle_since is None

    def test_idle_is_set(self, session, monkeypatch):
        monkeypatch.setattr('mita.providers.openstack.create_node', Mock())
        session.app.post_json(
            '/api/nodes/',
            params={
                'name': 'wheezy-slave',
                'provider': 'openstack',
                'keyname': 'ci-key',
                'image_name': 'beefy-wheezy',
                'size': '3xlarge',
                'script': '#!/bin/bash echo hello world! %s',
                'labels': ['wheezy', 'amd64'],
            }
        )
        node = Node.get(1)
        session.app.post('/api/nodes/%s/idle' % node.identifier)
        node = Node.get(1)
        assert node.idle_since is not None

    def test_make_node_active(self, session, monkeypatch):
        monkeypatch.setattr('mita.providers.openstack.create_node', Mock())
        session.app.post_json(
            '/api/nodes/',
            params={
                'name': 'wheezy-slave',
                'provider': 'openstack',
                'keyname': 'ci-key',
                'image_name': 'beefy-wheezy',
                'size': '3xlarge',
                'script': '#!/bin/bash echo hello world! %s',
                'labels': ['wheezy', 'amd64'],
            }
        )
        node = Node.get(1)
        session.app.post('/api/nodes/%s/idle' % node.identifier)
        node = Node.get(1)
        assert node.idle_since is not None
        session.app.post('/api/nodes/%s/active' % node.identifier)
        node = Node.get(1)
        assert node.idle_since is None
