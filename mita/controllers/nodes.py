from pecan import expose, abort, request
import logging
from mita.models import Node
from mita import providers
from mita.util import NodeState

logger = logging.getLogger(__name__)


class NodeController(object):

    def __init__(self, node_name):
        self.node_name = node_name
        self.node = Node.query.filter_by(name=node_name).first()

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
        # create from the cloud provider
        logger.warning('creating node with details: %s' % str(request.json))

        # Before creating a node, check if it has already been created by us:
        name = request.json['name']
        keyname = request.json['keyname']
        image_name = request.json['image_name']
        size = request.json['size']
        labels = request.json['labels']
        script = request.json['script']
        existing_nodes = Node.filter_by(
            name=name,
            keyname=keyname,
            image_name=image_name,
            size=size,
        ).all()

        matching_nodes = [n for n in existing_nodes if n.labels_match(labels)]
        if not matching_nodes:  # we don't have anything that matches this that has been ever created
            logger.info('requested node does not exist, will create one')
            # slap the UUID into the new node details
            import uuid
            _id = str(uuid.uuid4())
            request.json['name'] = "%s+%s" % (name, _id)
            # try to slap it into the script, it is not OK if we are not allowed to, assume we should
            try:
                request.json['script'] = script % _id
            except TypeError:
                logger.error('attempted to add a UUID to the script but failed')
                logger.error('ensure that a formatting entry exists, like: %%s')
                return  # do not add anything if we haven't been able to format
            created_node = provider.create_node(**request.json)
            # FIXME: this needs some unique name or identifier, maybe the mix
            # of names and tags? We need to use the returned object to slap the ID
            # into the database too
            # create it in the database
            #Node(created_node, **request.json)
            request.json.pop('name')
            Node(name=name, identifier=_id, node_obj=created_node, **request.json)

    @expose('json')
    def _lookup(self, node_name, *remainder):
        return NodeController(node_name), remainder
