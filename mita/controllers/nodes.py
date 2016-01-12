from copy import deepcopy
from datetime import datetime
import logging
import uuid

import jenkins
from pecan import expose, abort, request, conf
from mita.models import Node
from mita import providers
from mita.util import NodeState
from mita.exceptions import CloudNodeNotFound

logger = logging.getLogger(__name__)


class NodeController(object):

    def __init__(self, identifier):
        self.identifier = identifier
        self.node = Node.query.filter_by(identifier=identifier).first()

    @expose(generic=True, template='json')
    def index(self):
        if not self.node:
            abort(404)

    @expose('json')
    def active(self):
        """
        Mark the node as active by setting idle_since to None.
        """
        if not self.node:
            abort(404, 'could not find UUID: %s' % self.identifier)
        if self.node.idle_since is None:
            return
        logger.info("Marking %s as active." % self.node.identifier)
        self.node.idle_since = None

    @expose('json')
    def idle(self):
        """
        perform a check on the status of the current node, verifying how long
        it has been idle (if at all) marking the current timestamp since idle
        and determine if the node needs to be terminated.
        """
        if not self.node:
            abort(404, 'could not find UUID: %s' % self.identifier)
        provider_for_node = conf.nodes[self.node.name]['provider']
        provider = providers.get(provider_for_node)
        if request.method != 'POST':
            abort(405)
        now = datetime.utcnow()
        if self.node.idle:
            # it was idle before so check how many seconds since it was lazy.
            # `idle` is a property that will only be true-ish if idle_since has
            # been set.
            difference = now - self.node.idle_since
            if difference.seconds > 600:  # 10 minutes
                # we need to terminate this couch potato
                logger.info("Destroying node: %s" % self.node.cloud_name)
                try:
                    provider.destroy_node(name=self.node.cloud_name)
                except CloudNodeNotFound:
                    logger.info("node does not exist in cloud provider")
                # FIXMEEEEEEEE
                jenkins_url = conf.jenkins['url']
                jenkins_user = conf.jenkins['user']
                jenkins_token = conf.jenkins['token']
                conn = jenkins.Jenkins(jenkins_url, jenkins_user, jenkins_token)
                logger.info("Deleting node in jenkins: %s" % self.node.jenkins_name)
                conn.delete_node(self.node.jenkins_name)
                # delete from our database
                self.node.delete()

        else:  # mark it as being idle
            self.node.idle_since = now

    # FIXME: validation is needed here
    @expose('json')
    def delete(self):
        if request.method != 'POST':
            abort(405)
        if not self.node:
            abort(404)
        provider = providers.get(request.json['provider'])
        try:
            # destroy from the cloud provider
            destroyed = provider.destroy_node(**request.json)
            if not destroyed:
                # FIXME: this needs to return a proper reponse, not just a 500
                abort(500)
            # delete from the database
            self.node.delete()
        # FIXME: catch the exception from libcloud here
        except Exception:
            # find a way to REALLY sound the alarm because
            # if we can't delete it means that the user is going
            # to pay for a resource it should no longer exist
            abort(500)

    @expose('json')
    def status(self, **kw):
        # since this is a read-only request via GET we need to ask for query
        # args to determine the right node because the name alone is not good
        # enoug (we might have more than one node named 'centos6' for example.
        provider = providers.get(request.json['provider'])
        status = provider.node_status(self.node_name, **kw)
        state = NodeState[status]
        state_int = NodeState[state]
        return {'status': state, 'status_int': state_int}


class NodesController(object):

    @expose('json')
    def index(self):
        provider = providers.get(request.json['provider'])
        # request.json is read-only, since we are going to add extra metadata
        # to get the classes created, make a clean copy
        _json = deepcopy(request.json)

        # Before creating a node, check if it has already been created by us:
        name = _json['name']
        keyname = _json['keyname']
        image_name = _json['image_name']
        size = _json['size']
        labels = _json['labels']
        script = _json['script']
        existing_nodes = Node.filter_by(
            name=name,
            keyname=keyname,
            image_name=image_name,
            size=size,
        ).all()

        # slap the UUID into the new node details
        _id = str(uuid.uuid4())
        _json['name'] = "%s__%s" % (name, _id)
        # try to slap it into the script, it is not OK if we are not allowed to, assume we should
        try:
            _json['script'] = script % _id
        except TypeError:
            logger.error('attempted to add a UUID to the script but failed')
            logger.error(
                'ensure that a formatting entry for %s["script"] exists, like: %%s' % name
            )
            return  # do not add anything if we haven't been able to format

        logger.info('checking if an existing node matches the labels')
        matching_nodes = [n for n in existing_nodes if n.labels_match(labels)]
        if not matching_nodes:  # we don't have anything that matches this that has been ever created
            logger.info('no matching nodes were found, will create one')
            logger.warning('creating node with details: %s' % str(_json))
            provider.create_node(**_json)
            _json.pop('name')
            Node(
                name=request.json['name'],
                identifier=_id,
                **_json
            )
        else:
            logger.info('found existing nodes that match labels')
            now = datetime.utcnow()
            # we have something that matches, go over all of them and check:
            # if *all of them* are over 8 (by default) minutes since creation.
            # that means that they are probably busy, so create a new one
            for n in matching_nodes:
                difference = now - n.created
                if difference.seconds < 480:  # 8 minutes
                    logger.info('a node was already created in the past 8 minutes')
                    logger.info('will not create one')
                    return
                    # FIXME: need to check with cloud provider and see if this
                    # node is running, otherwise it means this node is dead and
                    # should be removed from the DB
            logger.info('no nodes created recently, will create a new one')
            provider.create_node(**_json)
            _json.pop('name')
            Node(
                name=request.json['name'],
                identifier=_id,
                **_json
            )

    @expose('json')
    def _lookup(self, node_name, *remainder):
        return NodeController(node_name), remainder
