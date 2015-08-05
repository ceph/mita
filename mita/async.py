import pecan
from celery import Celery
from datetime import timedelta
import jenkins
import os
import logging
from mita import util
logger = logging.getLogger(__name__)


def get_pecan_config():
    try:
        os.environ['PECAN_CONFIG']
    except KeyError:
        here = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.abspath(os.path.join(here, '../config/config.py'))
        return config_path


pecan.configuration.set_config(get_pecan_config())
app = Celery('mita.async', broker='amqp://guest@localhost//')


def infer_labels(task_name):
    values = task_name.split(',')
    labels = [v.split('=')[-1] for v in values]
    return labels


def match_node_from_labels(labels, configured_nodes):
    def labels_exist(config):
        for l in labels:
            if l not in config:
                return False
        return True

    for node, metadata in configured_nodes.items():
        if labels_exist(metadata['labels']):
            return node


@app.task
def check_queue():
    jenkins_url = app.conf.jenkins['url']
    jenkins_user = app.conf.jenkins['user']
    jenkins_token = app.conf.jenkins['token']
    conn = jenkins.Jenkins(jenkins_url, jenkins_user, jenkins_token)
    result = conn.get_queue_info()
    if result:
        for task in result:
            if task['stuck']:
                logger.info('found stuck task with name: %s' % task['task']['name'])
                labels = infer_labels(task['task']['name'])
                logger.info('inferred labels as: %s' % str(labels))
                node_name = match_node_from_labels(labels)
                if node_name:
                    logger.info('matched a node name to config: %s' % node_name)
                    # TODO: this should talk to the pecan app over HTTP using
                    # the `app.conf.pecan_app` configuration entry
                    util.create_node(node_name, **pecan.conf.nodes[node_name])
                else:
                    logger.warning('could not match a node name to config for labels')


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'add-every-30-seconds': {
            'task': 'async.check_queue',
            # FIXME: no way we want this to be 10 seconds
            'schedule': timedelta(seconds=10),
        },
    },
    nodes=pecan.conf.nodes,
    pecan_app=pecan.conf.server,
)
