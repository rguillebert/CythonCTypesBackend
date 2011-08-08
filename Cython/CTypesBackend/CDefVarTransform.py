from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.TreeFragment import TreeFragment
from Cython.Compiler.Nodes import CPtrDeclaratorNode, CArrayDeclaratorNode

class CDefVarTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def _get_type_node(self, decl, base_type):
        """ Returns the ctypes node required to get the type corresponding to the node """

        if isinstance(decl, CPtrDeclaratorNode):
            tf = TreeFragment(u'ctypes.POINTER(DUMMY)').root.stats[0].expr
            tf.args = [self._get_type_node(decl.base, base_type)]
            return tf

        if isinstance(decl, CArrayDeclaratorNode):
            tf = TreeFragment(u'DUMMY * %s' % (decl.dimension.value,)).root.stats[0].expr
            tf.operand1 = self._get_type_node(decl.base, base_type)
            return tf

        if base_type.is_basic_c_type:
            return TreeFragment(u'ctypes.c_%s' % (base_type.name,)).root.stats[0].expr
        else:
            return TreeFragment(u'%s' % (base_type.name,)).root.stats[0].expr

    def _get_ptr_name(self, decl):
        """ Returns the name of the pointer variable """
        return decl.name if hasattr(decl, 'name') else self._get_ptr_name(decl.base)

    def _get_vardefnode(self, decl, base_type):
        if isinstance(decl, CPtrDeclaratorNode):
            name = self._get_ptr_name(decl)
        elif isinstance(decl, CArrayDeclaratorNode):
            name = decl.base.name
        else:
            name = decl.name
        tf = TreeFragment(u'%s = DUMMY()' % (name,)).root.stats[0]
        tf.rhs.function = self._get_type_node(decl, base_type)
        return tf

    def visit_CVarDefNode(self, node):
        nodes = []
        for decl in node.declarators:
            nodes.append(self._get_vardefnode(decl, node.base_type))
        return nodes
