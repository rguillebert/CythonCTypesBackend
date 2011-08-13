from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import SingleAssignmentNode, CascadedAssignmentNode, InPlaceAssignmentNode, ParallelAssignmentNode
from Cython.Compiler.ExprNodes import AttributeNode, NameNode
from Cython.Compiler.PyrexTypes import CStructOrUnionType
from Cython.Compiler.TreeFragment import TreeFragment

class CDefVarManipulationTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    c_type_to_ctypes_type_dict = {
            'char' : 'char',
            'short' : 'short',
            'unsigned short' : 'ushort',
            'int' : 'int',
            'unsigned int' : 'uint',
            'long' : 'long',
            'unsigned long' : 'ulong',
            'PY_LONG_LONG' : 'longlong',
            'unsigned PY_LONG_LONG' : 'ulonglong',
            'Py_ssize_t' : 'int',
    }

    def is_structure_field(self, node):
        return isinstance(node, AttributeNode) and isinstance(node.obj.type, CStructOrUnionType)

    def is_arg(self, node):
        return hasattr(node, "entry") and node.entry != None and node.entry.is_arg

    def is_basic_C_type(self, node):
        return node.type != None and (node.type.is_numeric or node.type.is_string)

#    def visit_AssignmentNode(self, node):
#        if isinstance(node, SingleAssignmentNode) or isinstance(node, InPlaceAssignmentNode):
#            if not (self.is_structure_field(node.lhs) or self.is_arg(node.lhs)) and self.is_basic_C_type(node.lhs):
#                node.lhs = AttributeNode(0, obj=node.lhs, attribute=u"value")
#        elif isinstance(node, CascadedAssignmentNode):
#            new_lhs_list = []
#            for lhs in node.lhs_list:
#                if not (self.is_structure(lhs) or self.is_arg(lhs)) and self.is_basic_C_type(lhs):
#                    new_lhs_list.append(AttributeNode(0, obj=lhs, attribute=u"value"))
#                else:
#                    new_lhs_list.append(lhs)
#            node.lhs_list = new_lhs_list
#        elif isinstance(node, ParallelAssignmentNode):
#            new_stats = []
#            for assnode in node.stats:
#                new_stats.append(self.visit_AssignmentNode(assnode))
#            node.stats = new_stats
#        self.visitchildren(node)
#        return node

    def visit_NameNode(self, node):
        if self.is_basic_C_type(node):
            return AttributeNode(0, obj=node, attribute=u"value")
        return node

    def visit_CoerceToPyTypeNode(self, node):
        self.visitchildren(node)
        return node.arg

    def visit_CoerceFromPyTypeNode(self, node):
        self.visitchildren(node)
        return node.arg
