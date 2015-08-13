from libcloud.compute import types
from pecan import conf


def node_state_map():
    """
    creates a forward and reverse mapping of node states assumes values for
    states are unique integers

    we need a way to map a state *name* to its value and back and libcloud
    doesn't do this for us unless we call its tostring() and fromstring()
    methods but that is ugly.
    """
    mapping = {}
    for k, v in types.NodeState.__dict__.items():
        mapping[k] = v
        mapping[v] = k
    return mapping


NodeState = node_state_map()


def get_key(_dict, key, fallback=None):
    if key in _dict:
        return key
    return fallback or None

# TODO: all these need proper logging
# Stuck Queue Processors


def match_node(string):
    """
    Determine what node, if any, is needed from a given state of a Jenkins
    Queue. There are three distinct states from the API, so process it and
    determine if we are able to match it to a configured node.
    """
    busy_summary = lambda string: from_label if string.starswith('Waiting for') else None
    offline_summary = lambda string: from_offline_label if string.starswith('All nodes of label') else None
    offline_summary = lambda string: from_offline_node if string.endswith('is offline') else None
    for processor in [busy_summary, offline_summary, offline_summary]:
        if processor:
            return processor(string)


def from_label(string):
    """
    Behaves with some duality because both `BecauseLabelIsBusy` and
    `BecauseNodeIsBusy` have the same status. So it first will try to match
    a node by node name (a key in the configuration) and if it fails, it will
    go after labels.

    String to process::

        "Waiting for next available executor on {0}"
    """
    try:
        node_or_label = string.split()[-1]
    except IndexError:
        return None

    node_from_label = match_node_from_label(node_or_label)
    configured_nodes = conf['nodes'].to_dict()
    # node_or_label can be a node as a key in the config, so try to get that
    # first, and use the match from labels as a fallback. Try first with no
    # sanitizing of the node name, and if that doesn't work, try by splitting
    # on possible use of '+IP'
    match = get_key(configured_nodes, node_or_label) or get_key(configured_nodes, node_from_label)
    if match is None:
        clean_node = node_or_label.split('+')[0]
        match = get_key(configured_nodes, clean_node)
    return match


def from_offline_label(string):
    """
    String to process::

        u"All nodes of label \u2018{0}\u2019 are offline"
    """
    # effing unicode to have nice cute quotes in the UI
    to_remove = [u'\u2018', u'\u2019']
    for i in to_remove:
        string = string.replace(i, '')
    label = string.split()[-3]
    return match_node_from_label(label)


def from_offline_node(string):
    """
    String to process::

        "{0} is offline"
    """
    node = string.split()[0]
    configured_nodes = conf['nodes'].to_dict()
    # node can be a node as a key in the config, so try to get that first. Try
    # first with no sanitizing of the node name, and if that doesn't work, try
    # by splitting on possible use of '+IP'
    match = get_key(configured_nodes, node)
    if match is None:
        node = node.split('+')[0]
        match = node if node in configured_nodes else None
    return match


def match_node_from_label(label, configured_nodes=None):
    configured_nodes = configured_nodes or conf['nodes'].to_dict()
    for node, metadata in configured_nodes.items():
        if label in metadata['labels']:
            return node


# XXX we don't need these anymore, I think?
def infer_labels(task_name):
    """
    Jenkins uses the job name mingled with labels, so this function trims the
    string and sanitizes it so that clean labels can be consumed.
    """
    values = task_name.split(',')
    labels = [v.split('=')[-1] for v in values]
    return labels


def match_node_from_labels(labels, configured_nodes):
    """
    Given a list of labels, map them to a configured node type so that it can
    be created. All the labels must exist in the configured node
    """
    def labels_exist(config):
        for l in labels:
            if l not in config:
                return False
        return True

    for node, metadata in configured_nodes.items():
        if labels_exist(metadata['labels']):
            return node
