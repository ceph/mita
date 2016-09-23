from pecan import expose
from mita.controllers import nodes, health


class ApiController(object):

    nodes = nodes.NodesController()


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    api = ApiController()
    health = health.HealthController()
