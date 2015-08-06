from pecan import expose, abort, request
from mita.models import Node
from mita import providers
from mita.util import NodeState


class NodeController(object):

    def __init__(self, node_name):
        self.node_name = node_name
        self.node = Node.query.filter_by(name=node_name).first()

    @expose('json')
    def create(self):
        if request.method != 'POST':
            abort(405)
        provider = providers.get(request.json['provider'])
        # create from the cloud provider
        created_node = provider.create_node(**request.json)
        # FIXME: this needs some unique name or identifier, maybe the mix
        # of names and tags? We need to use the returned object to slap the ID
        # into the database too
        # create it in the database
        Node(created_node, **request.json)

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
    def _lookup(self, node_name, *remainder):
        return NodeController(node_name), remainder
