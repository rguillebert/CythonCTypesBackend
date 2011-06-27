from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.TreeFragment import TreeFragment
from Cython.Compiler.Nodes import CPtrDeclaratorNode

class CDefVarTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CVarDefNode(self, node):
        nodes = []
        if node.base_type.is_basic_c_type:
            for decl in node.declarators:
                if isinstance(decl, CPtrDeclaratorNode):
                    nodes.append(TreeFragment(u'%s = None' % (decl.base.name,)).root.stats[0])
                else:
                    nodes.append(TreeFragment(u'%s = ctypes.c_%s()' % (decl.name, node.base_type.name)).root.stats[0])
        else:
            for decl in node.declarators:
                if isinstance(decl, CPtrDeclaratorNode):
                    nodes.append(TreeFragment(u'%s = None' % (decl.base.name,)).root.stats[0])
                else:
                    nodes.append(TreeFragment(u'%s = %s()' % (decl.name, node.base_type.name)).root.stats[0])
        return nodes
