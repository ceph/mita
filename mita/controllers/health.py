from pecan import expose, abort

from mita import checks


class HealthController(object):

    @expose()
    def index(self):
        if not checks.is_healthy():
            abort(500)
