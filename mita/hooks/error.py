import logging
from webob.exc import WSGIHTTPException
from pecan.hooks import PecanHook


log = logging.getLogger(__name__)


class CustomErrorHook(PecanHook):
    """
    Only needed for prod environments where it looks like multi-worker servers
    will swallow exceptions. This will ensure a traceback is logged correctly.
    """
    def get_controller(self, state):
        '''
        Retrieves the actual controller name from the application
        Specific to Pecan (not available in the request object)
        '''
        return state.controller.__str__().split()[2]

    def on_error(self, state, exc):
        if isinstance(exc, WSGIHTTPException):
            if exc.code == 404:
                log.error("Not Found: %s" % state.request.url)
                return
            # explicit redirect codes that should not be handled at all by this
            # utility
            elif exc.code in [300, 301, 302, 303, 304, 305, 306, 307, 308]:
                return

        path = state.request.path
        controller = self.get_controller(state)

        log.error('unhandled error by controller: %s', controller)
        log.exception('request path %s', path)
