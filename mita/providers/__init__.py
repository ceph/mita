import logging
import openstack


logger = logging.getLogger(__name__)


def get(backend):
    module = _get_provider(backend)
    if not module:
        logger.error('unsupported provider was requested: %s' % backend)
        raise

    return module


def _get_provider(backend):
    if not backend:
        return

    providers = {
        'openstack': openstack,
        }

    return providers.get(backend)
