from mita.controllers import nodes
from datetime import timedelta, datetime
from mita.models import Node
from mita.tests.conftest import fake_jenkins


class TestNodesController(object):

    def test_create_new_node(self, session):
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

    def test_idle_is_unset(self, session):
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

    def test_idle_is_set(self, session):
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

    def test_make_node_active(self, session):
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


class TestNodeDeletion(object):

    def test_make_node_active(self, session):
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
        uuid = node.identifier
        # delete it
        session.app.post_json('/api/nodes/%s/delete/' % uuid, params={})
        assert Node.get(1) is None

    def test_node_not_in_jenkins_gets_skipped_(self, session, monkeypatch):
        fake_conn = fake_jenkins()
        fake_conn.node_exists = lambda x: True
        monkeypatch.setattr(nodes, "jenkins_connection", lambda *a: fake_conn)

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
        # make it idle for more than a day
        node.idle_since = datetime.utcnow() - timedelta(seconds=2000)
        session.commit()
        session.app.post('/api/nodes/%s/idle/' % node.identifier)
        assert Node.get(1) is not None

    def test_node_gets_skipped_not_idle(self, session, monkeypatch):
        fake_conn = fake_jenkins()
        fake_conn.node_exists = lambda x: True
        fake_conn.get_node_info = lambda x: {'idle': False}
        monkeypatch.setattr(nodes, "jenkins_connection", lambda *a: fake_conn)

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
        # make it idle for more than a day
        node.idle_since = datetime.utcnow() - timedelta(seconds=2000)
        session.commit()
        session.app.post('/api/nodes/%s/idle/' % node.identifier)
        assert Node.get(1) is not None

    def test_node_gets_destroyed(self, session, monkeypatch):
        fake_conn = fake_jenkins()
        fake_conn.node_exists = lambda x: True
        fake_conn.get_node_info = lambda x: {'idle': True}
        monkeypatch.setattr(nodes, "jenkins_connection", lambda *a: fake_conn)

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
        # make it idle for more than a day
        node.idle_since = datetime.utcnow() - timedelta(seconds=2000)
        session.commit()
        session.app.post('/api/nodes/%s/idle/' % node.identifier)
        assert Node.get(1) is None
