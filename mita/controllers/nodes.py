from copy import deepcopy
from datetime import datetime
import logging
import uuid

from pecan import expose, abort, request, conf
from mita.models import Node
from mita.tasks import delete_node
from mita.connections import jenkins_connection
from mita import providers, models
from mita.util import NodeState, delete_jenkins_node, delete_provider_node
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
            if difference.seconds > 1200:  # 20 minutes
                # we need to terminate this couch potato
                logger.info("Destroying node: %s" % self.node.cloud_name)
                try:
                    provider.destroy_node(name=self.node.cloud_name)
                except CloudNodeNotFound:
                    logger.info("node does not exist in cloud provider")
                conn = jenkins_connection()
                if conn.node_exists(self.node.jenkins_name):
                    logger.info("Deleting node in jenkins: %s" % self.node.jenkins_name)
                    conn.delete_node(self.node.jenkins_name)
                # delete from our database
                self.node.delete()

        else:  # mark it as being idle
            self.node.idle_since = now

    @expose('json')
    def delete(self):
        if request.method != 'POST':
            abort(405)
        if not self.node:
            abort(404)
        # XXX we need validation here
        # XXX WE REALLY NEED VALIDATION HERE
        try:
            delay = request.json.get('delay', 0)
        # simplejson.decoder.JSONDecodeError inherits from ValueError which is
        # the same that the builtin Python json handler will raise when no JSON
        # is passed in.
        except ValueError:
            delay = 0
        if delay:
            delete_node.apply_async(
                (self.node.id,),
                countdown=delay)
        else:
            delete_provider_node(
                providers.get(self.node.provider),
                self.node.cloud_name
            )
            delete_jenkins_node(self.node.jenkins_name)
            self.node.delete()

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
        count = _json.get('count', 1)
        # a buffered count is 3/4 what is needed rounded up
        buffered_count = int(round(count * 0.75))
        existing_nodes = Node.filter_by(
            name=name,
            keyname=keyname,
            image_name=image_name,
            size=size,
        ).all()

        # try to slap it into the script, it is not OK if we are not allowed to, assume we should
        # this is just a validation step, should be taken care of by proper schema validation.
        try:
            script % '0000-aaaaa'
        except TypeError:
            logger.error('attempted to add a UUID to the script but failed')
            logger.error(
                'ensure that a formatting entry for %s["script"] exists, like: %%s' % name
            )
            return  # do not add anything if we haven't been able to format

        logger.info('checking if an existing node matches required labels: %s', str(labels))
        matching_nodes = [n for n in existing_nodes if n.labels_match(labels)]
        if not matching_nodes:  # we don't have anything that matches this that has been ever created
            logger.info('job needs %s nodes to get unstuck', count)
            logger.info(
                'no matching nodes were found, will create new ones. count: %s',
                buffered_count
            )
            for i in range(buffered_count):
                # slap the UUID into the new node details
                node_kwargs = deepcopy(request.json)
                _id = str(uuid.uuid4())
                node_kwargs['name'] = "%s__%s" % (name, _id)
                node_kwargs['script'] = script % _id

                provider.create_node(**node_kwargs)
                node_kwargs.pop('name')
                Node(
                    name=name,
                    identifier=_id,
                    **node_kwargs
                )
                models.commit()
        else:
            logger.info('found existing nodes that match labels: %s', len(matching_nodes))
            now = datetime.utcnow()
            # we have something that matches, go over all of them and check:
            # if *all of them* are over 6 (by default) minutes since creation.
            # that means that they are probably busy, so create a new one
            already_created_nodes = 0
            for n in matching_nodes:
                difference = now - n.created
                if difference.seconds < 360:  # 6 minutes
                    already_created_nodes += 1
            if already_created_nodes >= count:
                logger.info('job needs %s nodes to get unstuck', count)
                logger.info(
                    'but there are %s node(s) already created 6 minutes ago',
                    already_created_nodes
                )
                logger.info('will not create one')
                return
            logger.info('job needs %s nodes to get unstuck', count)
            logger.info(
                'no nodes created recently enough, will create new ones. count: %s',
                buffered_count
            )
            for i in range(buffered_count):
                # slap the UUID into the new node details
                node_kwargs = deepcopy(request.json)
                _id = str(uuid.uuid4())
                node_kwargs['name'] = "%s__%s" % (name, _id)
                node_kwargs['script'] = script % _id

                provider.create_node(**node_kwargs)
                node_kwargs.pop('name')
                Node(
                    name=name,
                    identifier=_id,
                    **node_kwargs
                )
                models.commit()

    @expose('json')
    def _lookup(self, node_name, *remainder):
        return NodeController(node_name), remainder
