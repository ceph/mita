from pecan import expose
from mita.controllers import node


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    nodes = node.NodesController()

