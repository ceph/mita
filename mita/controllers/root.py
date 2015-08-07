from pecan import expose
from mita.controllers import nodes


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    nodes = nodes.NodesController()

