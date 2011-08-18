from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CSimpleBaseTypeNode

class CDefToDefTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CArgDeclNode(self, node):
        node.base_type = CSimpleBaseTypeNode()
        return node
