from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.TreeFragment import TreeFragment
from Cython.Compiler.Nodes import CPtrDeclaratorNode, CArrayDeclaratorNode
from Cython.Compiler.ExprNodes import NameNode, AttributeNode, SimpleCallNode

class CDefVarTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    
    __ctypes_declare_node = AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_func")
    
    def _get_type_node(self, decl, base_type, is_sub_call=False):
        """ Returns the ctypes node required to get the type corresponding to the node """

        
        if is_sub_call:
            root = u'%s'
        else:
            root = u'cython.ctypes_declare(%s)'
            
        if isinstance(decl, CPtrDeclaratorNode):
            numPointer = 0
            while isinstance(decl, CPtrDeclaratorNode):
                numPointer += 1
                decl = decl.base
            subType = self._get_type_node(decl, base_type, is_sub_call=True)
            pointerNode = SimpleCallNode(0,
                         child_attrs=[],
                         function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_pointer"),
                         args=[subType, TreeFragment(u'%d' % numPointer).root.stats[0].expr])
            if not is_sub_call:
                subType = SimpleCallNode(0,
                         child_attrs=[],
                         function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_declare"),
                         args=[pointerNode])
            return subType

        if isinstance(decl, CArrayDeclaratorNode):
            tf = TreeFragment(root % (u'DUMMY * %s' % (decl.dimension.value,))).root.stats[0].expr
            
            if is_sub_call:
                tf.operand1 = self._get_type_node(decl.base, base_type, is_sub_call=True)
            else:
                tf.args[0].operand1 = self._get_type_node(decl.base, base_type, is_sub_call=True)
            return tf

        if base_type.is_basic_c_type:
            return TreeFragment(root % (u'ctypes.c_%s' % (base_type.name,))).root.stats[0].expr
        else:
            return TreeFragment(root % (u'%s' % (base_type.name,))).root.stats[0].expr

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
        tf = TreeFragment(u'%s = DUMMY' % (name,)).root.stats[0]
        tf.rhs = self._get_type_node(decl, base_type)
        return tf

    def visit_CVarDefNode(self, node):
        nodes = []
        for decl in node.declarators:
            nodes.append(self._get_vardefnode(decl, node.base_type))
        return nodes
