from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CSimpleBaseTypeNode

class CDefToDefTransform(VisitorTransform):
    # Does not really turns cdefed function into defed function, it justs kills
    # the arguments and the return types of the functions, we rely on the
    # CodeWriter to get 'def' instead of 'cdef'
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CFuncDefNode(self, node):
        oldbase_type = node.base_type
        node.base_type = CSimpleBaseTypeNode(0)
        node.base_type.name = None
        return node

    def visit_CArgDeclNode(self, node):
        oldbase_type = node.base_type
        node.base_type = CSimpleBaseTypeNode(0)
        node.base_type.name = None
        node.base_type.is_self_arg = oldbase_type.is_self_arg
        return node
