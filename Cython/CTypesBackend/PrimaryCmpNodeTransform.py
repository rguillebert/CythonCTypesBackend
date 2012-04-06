from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.ExprNodes import ImportNode, StringNode, NullNode
from Cython.Compiler.TreeFragment import TreeFragment


class PrimaryCmpNodeTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_PrimaryCmpNode(self, node):
        operator = node.operator
        if operator == u'is_not':
            node.operator = u'is not'
        if isinstance(node.operand1, NullNode) or isinstance(node.operand2, NullNode):
            if not isinstance(node.operand1, NullNode):
                node.operand1.attribute += u'.value'
            elif isinstance(node.operand2, NullNode):
                node.operand2.attribute += u'.value'
        return node
