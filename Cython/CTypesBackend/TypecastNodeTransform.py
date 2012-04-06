from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.ExprNodes import ImportNode, StringNode, NullNode, SimpleCallNode, AttributeNode, NameNode
from Cython.Compiler.TreeFragment import TreeFragment
from Cython.CTypesBackend.ExternDefTransform import cythonTypeToCtypes, ctypeToStr


class TypecastNodeTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_TypecastNode(self, node):
        return SimpleCallNode(0,
                               child_attrs=[],
                               function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_cast"),
                               args=[node.operand,
                                     NameNode(0, name=cythonTypeToCtypes(node, node.declarator)[2])])
