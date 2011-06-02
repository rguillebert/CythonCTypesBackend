from itertools import chain
from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CFuncDeclaratorNode, CVarDefNode, SingleAssignmentNode
from Cython.Compiler.ExprNodes import NameNode, AttributeNode, ListNode

def _make_ctypes_node(name, restype, arglist):
    stmts = []

    func_assign = SingleAssignmentNode(0)
    func_assign.lhs = NameNode(0, name=name)
    func_assign.rhs = AttributeNode(0, obj=NameNode(0, name=u"library"), attribute=name)

    func_argtypes = SingleAssignmentNode(0)
    func_argtypes.lhs = AttributeNode(0, obj=NameNode(0, name=name, attribute=u"argtypes"))
    func_argtypes.rhs = ListNode(0)
    func_argtypes.rhs.args = []
    for argdecl in arglist:
        assert argdecl.base_type.is_basic_c_type, "Type %s is not a C primitive type" % argdecl.base_type.name
        func_argtypes.rhs.args.append(AttributeNode(0, obj=NameNode(0, name=u"ctypes", attribute=u"c_" + argdecl.base_type.name)))

    assert restype.is_basic_c_type, "Type %s is not a C primitive type" % restype.name
    func_restype = SingleAssignmentNode(0)
    func_restype.lhs = AttributeNode(0, obj=NameNode(0, name=name, attribute=u"restype"))
    func_restype.rhs = AttributeNode(0, obj=NameNode(0, name=u"ctypes", attribute=u"c_" + restype.name))

    stmts.append(func_assign)
    stmts.append(func_argtypes)
    stmts.append(func_restype)
    return stmts

class ExternDefTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CDefExternNode(self, node):
        stats = []
        ctypes_nodes = []
        if hasattr(node.body, "stats"):
            # StatListNode
            stats = node.body.stats
        else:
            # Other Nodes
            stats.append(node.body)

        for defnode in stats:
            if isinstance(defnode, CVarDefNode):
                base_type = defnode.base_type
                for decl in defnode.declarators:
                    if isinstance(decl, CFuncDeclaratorNode):
                        # Function definition
                        ctypes_nodes.append(_make_ctypes_node(decl.base.name, base_type, decl.args))

        return list(chain(ctypes_nodes))
