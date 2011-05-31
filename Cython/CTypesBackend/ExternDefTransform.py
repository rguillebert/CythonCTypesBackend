from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CFuncDeclaratorNode, CVarDefNode

class ExternDefTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def visit_CDefExternNode(self, node):
        stats = []
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
                        print "%s %s(%s)" % (base_type.name, decl.base.name, ", ".join([arg.base_type.name for arg in decl.args]))

        return node
