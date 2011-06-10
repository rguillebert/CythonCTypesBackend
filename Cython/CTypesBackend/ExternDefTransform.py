import ctypes
from ctypes_configure import configure
from itertools import chain
from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CFuncDeclaratorNode, CVarDefNode, SingleAssignmentNode, CStructOrUnionDefNode, PyClassDefNode, StatListNode, PassStatNode, CPtrDeclaratorNode
from Cython.Compiler.ExprNodes import NameNode, AttributeNode, ListNode, NoneNode, TupleNode, StringNode, SimpleCallNode


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
            if base_type.is_basic_c_type:
                for decl in attr.declarators:
                    if isinstance(decl, CPtrDeclaratorNode):
                        # Pointer attribute
                        attr_list.append((str(decl.base.name), ctypes.POINTER(getattr(ctypes, "c_" + str(base_type.name)))))
                    else:
                        attr_list.append((str(decl.name), getattr(ctypes, "c_" + str(base_type.name))))
            else:
                for decl in attr.declarators:
                    if isinstance(decl, CPtrDeclaratorNode):
                        attr_list.append((str(decl.base.name), ctypes.POINTER(self.ctypes_struct_union_dict[str(base_type.name)])))
                    else:
                        attr_list.append((str(decl.name), self.ctypes_struct_union_dict[str(base_type.name)]))

        return attr_list

    def _make_ctypes_struct_union_class_node(self, type_name, type_class, union=False):
        field_list = ListNode(0)
        field_list.args = []
        for field in type_class._fields_:
            is_pointer = hasattr(field[1], "contents") # XXX: Maybe a better way should be found
            if is_pointer: field = (field[0], field[1]._type_)
            if field[1].__module__ == "ctypes":
                # Basic C types
                if is_pointer:
                    field_list.args.append(TupleNode(0, args=[
                            StringNode(0, value=field[0]),
                            SimpleCallNode(0, function=AttributeNode(0, obj=NameNode(0, name=u"ctypes"), attribute=u"POINTER"), args=[
                                AttributeNode(0,
                                    obj=NameNode(0, name=u"ctypes"),
                                    attribute=unicode(field[1].__name__))
                            ])
                        ]))
                else:
                    field_list.args.append(TupleNode(0, args=[
                        StringNode(0, value=field[0]),
                        AttributeNode(0,
                            obj=NameNode(0, name=u"ctypes"),
                            attribute=unicode(field[1].__name__))
                        ]))
            else:
                if is_pointer:
                    field_list.args.append(TupleNode(0, args=[
                            StringNode(0, value=field[0]),
                            SimpleCallNode(0, function=AttributeNode(0, obj=NameNode(0, name=u"ctypes"), attribute=u"POINTER"), args=[
                                NameNode(0, name=unicode(field[1].__name__))
                            ])
                        ]))
                else:
                    field_list.args.append(TupleNode(0, args=[
                        StringNode(0, value=field[0]),
                        NameNode(0, name=unicode(field[1].__name__))
                        ]))

        field_assign = SingleAssignmentNode(0, lhs=AttributeNode(0, obj=NameNode(0, name=unicode(type_name)), attribute=u"_fields_"), rhs=field_list)
        class_def = PyClassDefNode(0, unicode(type_name), TupleNode(0, args=[AttributeNode(0, obj=NameNode(0, name=u"ctypes"), attribute=u"Structure")]), None, StatListNode(0, stats=[PassStatNode(0)]))

        return class_def, field_assign

    def _make_ctypes_struct_union(self, include_file, name, attributes, union=False):
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

        # We create an empty structure before in the case where the structure as a pointer to itself
        class ctypes_struct(ctypes.Structure):
            pass
        ctypes_struct.__name__ = str(name)

        self.ctypes_struct_union_dict[str(name)] = ctypes_struct

        setattr(CConfigure, str(name), configure.Struct("struct " + str(name), self._make_struct_attr_list(attributes)))

        info = configure.configure(CConfigure)
        ctypes_struct._fields_ = info[str(name)]._fields_

        return str(name), ctypes_struct

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
        # TODO: Arrays
        # TODO: Unions
        struct_union_nodes = []
        struct_union_field_nodes = []
        func_nodes = []
        stats = node.body.stats

        for defnode in stats:
            if isinstance(defnode, CVarDefNode):
                base_type = defnode.base_type
                for decl in defnode.declarators:
                    if isinstance(decl, CFuncDeclaratorNode):
                        # Function definition
                        func_nodes.append(self._make_ctypes_func_node(decl.base.name, base_type, decl.args))
            elif isinstance(defnode, CStructOrUnionDefNode):
                if defnode.kind == "struct":
                    # Structure definition
                    struct_name, struct = self._make_ctypes_struct_union(node.include_file, defnode.name, defnode.attributes)
                    self.ctypes_struct_union_dict[struct_name] = struct
                    class_def, field_def = self._make_ctypes_struct_union_class_node(struct_name, struct)
                    struct_union_nodes.append(class_def)
                    struct_union_field_nodes.append(field_def)
                else:
                    # Union definition
                    assert False, "Union not supported yet"
                    struct_name, struct = self._make_ctypes_struct_union(node.include_file, defnode.name, defnode.attributes, union=True)
                    self.ctypes_struct_union_dict[struct_name] = struct
                    class_def, field_def = self._make_ctypes_struct_union_class_node(struct_name, struct, union=True)
                    struct_union_nodes.append(class_def)
                    struct_union_field_nodes.append(field_def)

        return list(chain(chain(*func_nodes), struct_union_nodes, struct_union_field_nodes))

    def visit_ModuleNode(self, node):
        self.ctypes_struct_union_dict = {}
        self.recurse_to_children(node)
        return node
