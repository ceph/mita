import ast
import logging
import re

log = logging.getLogger(__name__)


class UnsafeNodeType(Exception):
    ''' Unsafe node type found '''

    def __init__(self, nodetype):
        self.nodetype = nodetype

    def __str__(self):
        return self.__class__.__name__ + ': ' + self.nodetype


class myvisitor(ast.NodeVisitor):
    '''
    Collect all the Name nodes from an ast tree into self.names
    Also, raise UnsafeNodeType if anything but boolean expression node
    types are found in the expression.

    Used to analyze a Jenkins boolean expression, permitting only
    'safe' expressions, and accumulate a list of symbols that must
    be defined to True or False in order to evaluate it.
    '''

    # allow nodes only of these ast class types
    ALLOWED_TYPES = [
        'Module',
        'Expr',
        'BoolOp',
        'UnaryOp',
        'Name',
        'Load',
        'And',
        'Or',
        'Not',
    ]

    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self.names = set()

    def visit_Name(self, node):
        name = node.id
        self.names.add(name)

    def generic_visit(self, node):
        # filter every node through ALLOWED_TYPES
        if node.__class__.__name__ not in myvisitor.ALLOWED_TYPES:
            raise UnsafeNodeType(node.__class__.__name__)
        ast.NodeVisitor.generic_visit(self, node)


def pythonize_boolean(expr):
    ''' Translate a boolean expression from C-like operators to Python'''

    replacements = {
        '\s*&&\s*': ' and ',
        '\s*\|\|\s*': ' or ',
        '\s*!\s*': ' not ',
    }

    for search, repl in replacements.iteritems():
        expr = re.sub(search, repl, expr)
    # strip in case an operator was first on the line, otherwise
    # parse will throw IndentationError
    return expr.strip()


def validate_and_parse(expr):
    '''
    Collect names mentioned in expr using ast.parse and
    ast's NodeVisitor class, while validating expr for safety.
    Returns a set() of all noted names.
    '''
    try:
        tree = ast.parse(expr)
    except SyntaxError as e:
        log.warning(e)
        return set()

    visitor = myvisitor()
    try:
        visitor.visit(tree)
    except UnsafeNodeType as e:
        log.warning(e)
        return set()

    return visitor.names


def matching_nodes(expr, nodes):
    '''Returns a list of nodes that match expr'''
    # return value
    matching_nodes = list()

    expr = pythonize_boolean(expr)

    # collect all expr's names
    names = validate_and_parse(expr)
    if not names:
        return matching_nodes

    # all the names in expr, initialized to "False"
    symdict = {k: False for k in names}

    for nodename, metadata in nodes.iteritems():
        # copy for this particular slave
        localdict = dict(symdict)

        # Note labels supplied by nodename as 'True' in localdict
        # (we could limit this only to labels that already
        # exist in the expression, but there's not much point;
        # if the expression doesn't care it doesn't care in the
        # eval() below either)
        for label in metadata['labels']:
            localdict[label] = True

        # localdict is now the intersection of labels mentioned in expr
        # and labels supplied by node, with True/False set
        # appropriately for this node.
        if eval(expr, globals(), localdict) is True:
            matching_nodes.append(nodename)

    return matching_nodes
