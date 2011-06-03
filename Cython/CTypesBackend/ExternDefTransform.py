import ctypes
from ctypes_configure import configure
from itertools import chain
from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CFuncDeclaratorNode, CVarDefNode, SingleAssignmentNode, CStructOrUnionDefNode, PyClassDefNode, StatListNode
from Cython.Compiler.ExprNodes import NameNode, AttributeNode, ListNode, NoneNode, TupleNode, StringNode


class ExternDefTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def _make_ctypes_type_node(self, cythontype):
        """ Given a CSimpleBaseTypeNode, returns an AST Node corresponding to the ctypes type """
        if cythontype.is_basic_c_type:
            if cythontype.name == "void":
                return AttributeNode(0, obj=NameNode(0, name=u"ctypes"), attribute=NoneNode())
            return AttributeNode(0, obj=NameNode(0, name=u"ctypes"), attribute=u"c_" + cythontype.name)
        else:
            return NameNode(0, name=unicode(cythontype.name))

    def _make_struct_attr_list(self, attributes):
        attr_list = []

        for attr in attributes:
            base_type = attr.base_type
            assert base_type.is_basic_c_type, "Type %s is not a C primitive type" % cythontype.name
            for decl in attr.declarators:
                attr_list.append((str(decl.name),getattr(ctypes,"c_" + str(base_type.name))))

        return attr_list

    def _make_ctypes_struct_class_node(self, struct_name, struct_class):
        field_list = ListNode(0)
        field_list.args = []
        for field in struct_class._fields_:
            assert field[1].__module__ == "ctypes", "Type %s is not a C primitive type" % field
            field_list.args.append(TupleNode(0, args=[
                StringNode(0, value=field[0]),
                AttributeNode(0,
                    obj=NameNode(0, name=u"ctypes"),
                    attribute=unicode(field[1].__name__))
                ]))

        field_assign = SingleAssignmentNode(0, lhs=NameNode(0, name=u"_fields_"), rhs=field_list)

        return PyClassDefNode(0, unicode(struct_name), None, None, StatListNode(0, stats=[field_assign]))

    def _make_ctypes_struct(self, include_file, name, attributes):
        class CConfigure(object):
            _compilation_info_ = configure.ExternalCompilationInfo(
                    pre_include_lines = [],
                    includes = [str(include_file)],
                    include_dirs = [],
                    post_include_lines = [],
                    libraries = [],
                    library_dirs = [],
                    separate_module_sources = [],
                    separate_module_files = [],
                )

        setattr(CConfigure, str(name), configure.Struct("struct " + str(name), self._make_struct_attr_list(attributes)))
        info = configure.configure(CConfigure)
        return str(name), info[str(name)]

    def _make_ctypes_func_node(self, name, restype, arglist):
        stmts = []

        func_assign = SingleAssignmentNode(0)
        func_assign.lhs = NameNode(0, name=name)
        func_assign.rhs = AttributeNode(0, obj=NameNode(0, name=u"library"), attribute=name)

        func_argtypes = SingleAssignmentNode(0)
        func_argtypes.lhs = AttributeNode(0, obj=NameNode(0, name=name), attribute=u"argtypes")
        func_argtypes.rhs = ListNode(0)
        func_argtypes.rhs.args = []
        for argdecl in arglist:
            func_argtypes.rhs.args.append(self._make_ctypes_type_node(argdecl.base_type))

        func_restype = SingleAssignmentNode(0)
        func_restype.lhs = AttributeNode(0, obj=NameNode(0, name=name), attribute=u"restype")
        func_restype.rhs = self._make_ctypes_type_node(restype)

        stmts.append(func_assign)
        stmts.append(func_argtypes)
        stmts.append(func_restype)
        return stmts

    def visit_CDefExternNode(self, node):
        ctypes_nodes = []
        stats = node.body.stats

        for defnode in stats:
            if isinstance(defnode, CVarDefNode):
                base_type = defnode.base_type
                for decl in defnode.declarators:
                    if isinstance(decl, CFuncDeclaratorNode):
                        # Function definition
                        ctypes_nodes.append(self._make_ctypes_func_node(decl.base.name, base_type, decl.args))
            elif isinstance(defnode, CStructOrUnionDefNode):
                if defnode.kind == "struct":
                    struct_name, struct = self._make_ctypes_struct(node.include_file, defnode.name, defnode.attributes)
                    self.ctypes_struct_dict[struct_name] = struct
                    ctypes_nodes.append([self._make_ctypes_struct_class_node(struct_name, struct)])
                else:
                    assert False, "Unions not implemented for the moment"

        return list(chain(*ctypes_nodes))

    def visit_ModuleNode(self, node):
        self.ctypes_struct_dict = {}
        self.recurse_to_children(node)
        return node
