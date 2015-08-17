import pecan
from celery import Celery
from datetime import timedelta
import requests
import jenkins
import json
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


pecan.configuration.set_config(get_pecan_config(), overwrite=True)
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
    """
    Specifically checks for the status of the Jenkins queue. The docs are
    sparse here, but
    ``jenkins/core/src/main/resources/hudson/model/queue/CauseOfBlockage`` has
    the specific reasons this check needs:

    * *BecauseLabelIsBusy* Waiting for next available executor on {0}

    * *BecauseLabelIsOffline* All nodes of label \u2018{0}\u2019 are offline

    * *BecauseNodeIsBusy* Waiting for next available executor on {0}

    * *BecauseNodeLabelIsOffline* There are no nodes with the label \u2018{0}\u2019

    * *BecauseNodeIsOffline* {0} is offline

    The distinction is the need for a label or a node. In the case of a node,
    it will get matched directly to the nodes in the configuration, in case of a label
    it will go through the configured nodes and pick the first matched to its labels.

    Label needed example
    --------------------
    Jenkins queue reports that 'All nodes of label x86_64 are offline'. The
    configuration has::

        nodes: {
            'centos6': {
                ...
                'labels': ['x86_64', 'centos', 'centos6']
            }
        }

    Since 'x86_64' exists in the 'centos6' configured node, it will be sent off
    to create that one.

    Node needed example
    -------------------
    Jenkins reports that 'wheezy is offline'. The configuration has a few
    labels configured::

        nodes: {
            'wheezy': {
                ...
            }
            'centos6': {
                ...
            }
        }

    Since the key 'wheezy' matches the node required by the build system to
    continue it goes off to create it.
    """
    jenkins_url = app.conf.jenkins['url']
    jenkins_user = app.conf.jenkins['user']
    jenkins_token = app.conf.jenkins['token']
    conn = jenkins.Jenkins(jenkins_url, jenkins_user, jenkins_token)
    result = conn.get_queue_info()
    if result:
        for task in result:
            if task['stuck']:
                logger.info('found stuck task with name: %s' % task['task']['name'])
                logger.info('reason was: %s' % task['why'])
                node_name = util.match_node(task['why'])
                logger.info('inferred node as: %s' % str(node_name))
                if node_name:
                    logger.info('matched a node name to config: %s' % node_name)
                    # TODO: this should talk to the pecan app over HTTP using
                    # the `app.conf.pecan_app` configuration entry, and then follow this logic:
                    # * got asked to create a new node -> check for an entry in the DB for a node that
                    # matches the characteristics of it.
                    #  * if there is one already:
                    #    - check that if it has been running for more than N (configurable) minutes (defaults to 8):
                    #      * if it has, it means that it is probable busy already, so:
                    #        - create a new node in the cloud backend matching the characteristics needed
                    #      * if it hasn't, it means that it is still getting provisioned so:
                    #        - skip - do a log warning
                    #  * if there is more than one, and it has been more than
                    #    N (8) minutes since they got launched it is possible
                    #    that they are configured *incorrectly* and we should not
                    #    keep launching more, so log the warning and skip.
                    #    - now ask Jenkins about machines that have been idle
                    #      for N (configurable) minutes, and see if matches
                    #      a record in the DB for the characteristics that we are
                    #      being asked to create.
                    #      * if found/matched:
                    #        - log the warnings again, something is not working right.
                    node_endpoint = get_mita_api('nodes')
                    requests.post(node_endpoint, data=json.dumps(pecan.conf.nodes[node_name]))
                else:
                    logger.warning('could not match a node name to config for labels')


def get_mita_api(endpoint=None):
    """
    Puts together the API url for mita, so that we can talk to it. Optionally, the endpoint
    argument allows to return the correct url for specific needs. For example, to create a node:

        http://0.0.0.0/api/nodes/

    """
    server = pecan.conf['server']['host']
    port = pecan.conf['server']['port']
    base = "http://%s:%s/api" % (server, port)
    endpoints = {
        'nodes': '%s/nodes/' % base,
    }
    if endpoint:
        return endpoints[endpoint]
    return base


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
    jenkins=pecan.conf.jenkins
)
