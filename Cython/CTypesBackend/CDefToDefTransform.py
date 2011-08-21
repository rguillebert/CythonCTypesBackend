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
        node.base_type.is_self_arg = False
        self.strip_args_types(node.declarator.args)
        return node

    def visit_DefNode(self, node):
        self.strip_args_types(node.args)
        return node

    def strip_args_types(self, args):
        for arg in args:
            oldbase_type = arg.base_type
            arg.base_type = CSimpleBaseTypeNode(0)
            arg.base_type.name = None
            arg.base_type.is_self_arg = oldbase_type.is_self_arg
