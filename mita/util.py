from libcloud.compute import types

# we need a way to map a state *name* to its value and back
# and libcloud doesn't do this for us unless we call its tostring() and
# fromstring() methods but that is ugly.


def node_state_map():
    """
    creates a forward and reverse mapping of node states
    assumes values for states are unique integers
    """
    mapping = {}
    for k, v in types.NodeState.__dict__.items():
        mapping[k] = v
        mapping[v] = k
    return mapping


NodeState = node_state_map()
