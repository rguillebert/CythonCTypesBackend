from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.ExprNodes import ImportNode, StringNode
from Cython.Compiler.TreeFragment import TreeFragment


class CImportToImportTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CImportStatNode(self, node):
        tf = TreeFragment(u'import %s' % node.module_name).root.stats[0].rhs
        return tf

    def visit_FromCImportStatNode(self, node):
        imported_names = u', '.join([import_info[1] for import_info in node.imported_names])
        return TreeFragment(u'from %s import %s' % (node.module_name, imported_names)).root.stats[0]

    def visit_SingleAssignmentNode(self, node):
        if isinstance(node.rhs, ImportNode):
            return node.rhs
        else:
            return node
