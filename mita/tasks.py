import pecan
from celery import shared_task
import logging
from mita import util, models, providers
logger = logging.getLogger(__name__)

@shared_task
def delete_node(node_id):
    if hasattr(pecan.conf.sqlalchemy, 'engine') is False:
        # for some reason celery doesn't have this at this point so we need
        # to init the model and bind to a Session.
        models.init_model()
        models.start()
    node = models.Node.get(node_id)
    if not node:
        logger.warning('async node deletion could not be completed')
        logger.warning('%s node id no longer exists', node_id)
        return

    util.delete_provider_node(
        providers.get(node.provider),
        node.cloud_name
    )
    util.delete_jenkins_node(node.jenkins_name)
    node.delete()
    models.commit()
