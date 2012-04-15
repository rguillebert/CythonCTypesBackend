import ctypes
import ctypes.util
from ctypes_configure import configure
from itertools import chain
from Cython.Compiler.Visitor import VisitorTransform
from Cython.Compiler.Nodes import CFuncDeclaratorNode, CVarDefNode, SingleAssignmentNode, CStructOrUnionDefNode, PyClassDefNode, StatListNode, PassStatNode, CPtrDeclaratorNode, DecoratorNode, FuncDefNode, CArrayDeclaratorNode
from Cython.Compiler.ExprNodes import NameNode, AttributeNode, ListNode, NoneNode, TupleNode, StringNode, SimpleCallNode, ImportNode, CallNode
from Cython.Compiler.TreeFragment import TreeFragment
import ctypes
from ctypes import *
from Cython import Shadow
from distutils.errors import CompileError

cythonTypetoCtypes = {'char': ctypes.c_char,
 'double': ctypes.c_double,
 'float': ctypes.c_float,
 'int': ctypes.c_int,
 'long': ctypes.c_long,
 'longdouble': ctypes.c_longdouble,
 'longlong': ctypes.c_long,
 'short': ctypes.c_short,
 'size_t': ctypes.c_size_t,
 'uint': ctypes.c_uint,
 'ulong': ctypes.c_ulong,
 'ulonglong': ctypes.c_ulonglong,
 'ushort': ctypes.c_ushort,
 'void': None}

def ctypeToStr(ctype_t, default_str=''):
    if ctype_t is None:
        return 'None'
    if 'P_' in ctype_t.__name__:
        root = ctype_t.__name__[ctype_t.__name__.rfind('P_')+2:]
        if root in dir(ctypes):
            numPointer = ctype_t.__name__.count('P_')
            return u'cython.ctypes_pointer(ctypes.%(root)s,%(numPointer)s)' % vars()
    if ctype_t.__name__ not in dir(ctypes):
        return default_str
    return u'ctypes.' + ctype_t.__name__    

def cythonTypeToCtypes(cython_t, decl):
    base_type = cython_t.base_type
        
    if base_type.is_basic_c_type:
        field_type = cythonTypetoCtypes[base_type.name]
        field_type_str = ctypeToStr(cythonTypetoCtypes[base_type.name])
    else:
        field_type = None
        field_type_str = base_type.name
        
    if isinstance(decl, CPtrDeclaratorNode) or isinstance(decl, CArrayDeclaratorNode):
        field_name = getattr(decl.base, 'name', None)
    else:
        field_name = getattr(decl, 'name', None)
        
    numPointer = 0
    orig_field_type_str = field_type_str
    while isinstance(decl, CPtrDeclaratorNode):
        field_type = POINTER(field_type)
        numPointer += 1
        field_type_str = u'cython.ctypes_pointer(%s,%d)' % (orig_field_type_str, numPointer)
        decl = decl.base
        
    if isinstance(decl, CArrayDeclaratorNode):
        field_type *= int(decl.dimension.value)
        field_type_str += u' * %s' % decl.dimension.value
            
        
    return (field_name, field_type, field_type_str)
    
class ExternDefTransform(VisitorTransform):
    visit_Node = VisitorTransform.recurse_to_children

    def __init__(self, context):
        super(ExternDefTransform, self).__init__()
        self.context = context
        self.isInExternScope = False
        self.include_file = None
    def _ctypeToStr(self, ctype_t, default_str=''):
        if ctype_t is None:
            return 'None'
        if 'P_' in ctype_t.__name__:
            root = ctype_t.__name__[ctype_t.__name__.rfind('P_')+2:]
            if root in dir(ctypes):
                numPointer = ctype_t.__name__.count('P_')
                return u'cython.ctypes_pointer(ctypes.%(root)s,%(numPointer)s)' % vars()
        if ctype_t.__name__ not in dir(ctypes):
            return default_str
        return u'ctypes.' + ctype_t.__name__       
    def _cythonTypeToCtypes(self, cython_t, decl):
        base_type = cython_t.base_type
            
        if base_type.is_basic_c_type:
            field_type = cythonTypetoCtypes[base_type.name]
            field_type_str = self._ctypeToStr(cythonTypetoCtypes[base_type.name])
        else:
            field_type = None
            field_type_str = base_type.name
            
        if isinstance(decl, CPtrDeclaratorNode) or isinstance(decl, CArrayDeclaratorNode):
            field_name = getattr(decl.base, 'name', None)
        else:
            field_name = getattr(decl, 'name', None)
            
        numPointer = 0
        orig_field_type_str = field_type_str
        while isinstance(decl, CPtrDeclaratorNode):
            field_type = POINTER(field_type)
            numPointer += 1
            field_type_str = u'cython.ctypes_pointer(%s,%d)' % (orig_field_type_str, numPointer)
            decl = decl.base
            
        if isinstance(decl, CArrayDeclaratorNode):
            field_type *= int(decl.dimension.value)
            field_type_str += u' * %s' % decl.dimension.value
                
            
        return (field_name, field_type, field_type_str)
    
    def _get_actual_ctype(self, base_name, initial_type):
        class CConfigure(object):
            _compilation_info_ = configure.ExternalCompilationInfo(
                    pre_include_lines = [],
                    includes = [self.include_file],
                    include_dirs = self.context.options.include_path,
                    post_include_lines = [],
                    libraries = [],
                    library_dirs = [],
                    separate_module_sources = [],
                    separate_module_files = [],
                )
            
            c_type = configure.SimpleType(base_name, initial_type)
            
            
        info = configure.configure(CConfigure)
        return info['c_type']
    def _ctype_to_node(self, type_name):
        return NameNode(0, name=type_name)
    
    def _cython_type_to_ctypes_node(self, cython_t):
        ctype_name = self._cythonTypeToCtypes(cython_t, getattr(cython_t, 'declarator', None))[2]
#        ctype_t = getattr(ctypes, ctype_name)
#        
#        final_ctype_t = self._get_actual_ctype(cython_t.base_type.name, ctype_t)
#        ctype_final_name = ctypeToStr[final_ctype_t]
        ctype_final_name = ctype_name
        return self._ctype_to_node(ctype_final_name)
    
    def _find_libname(self, func_name):
        func_lib = None
        func_libname = None
        for lib_name in self.context.options.libraries:
            try:
                lib = ctypes.CDLL(ctypes.util.find_library(lib_name))
            except:
                # Hack necessary for some libaries?
                lib = ctypes.CDLL('.'.join(ctypes.util.find_library(lib_name).split('.')[:-1]))
            try:
                getattr(lib, func_name)
            except AttributeError:
                continue
            return lib_name

        if not func_lib:
            raise NameError("Function %s cannot be found" % func_name)
        
        return func_libname
    
    def _CFuncToFunc(self, declarator, restype):
        libname = self._find_libname(declarator.base.name)
        
        rhs=SimpleCallNode(0,
                         child_attrs=[],
                         function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_func"),
                         args=[NameNode(0, name="'%s'" % declarator.base.name), 
                               NameNode(0, name="'%s'" % libname), 
                               self._cython_type_to_ctypes_node(restype)] + [self._cython_type_to_ctypes_node(arg) for arg in declarator.args])
        return SingleAssignmentNode(0,
                                    lhs=NameNode(0, name=declarator.base.name),
                                    rhs=rhs)
    
    def visit_CVarDefNode(self, node): 
        if not self.isInExternScope:
            return node
        if len(node.declarators) < 1:
            return node
        
        declarator = node.declarators[0]
        if isinstance(declarator, CFuncDeclaratorNode):
            return self._CFuncToFunc(declarator, node)
        elif isinstance(declarator, CPtrDeclaratorNode):
            if isinstance(declarator.base, CFuncDeclaratorNode):
                node.declarator = declarator
                return self._CFuncToFunc(declarator.base, node)
        else:
            return node
    
    def _make_struct_attr_list(self, attributes):
        fields = []
        for field in attributes:
            for decl in field.declarators:
                fields.append(self._cythonTypeToCtypes(field, decl))
        
        return fields
            
    def _make_ctypes_struct_union(self, name, attributes):
        class CConfigure(object):
            _compilation_info_ = configure.ExternalCompilationInfo(
                    pre_include_lines = [],
                    includes = [self.include_file] if self.include_file else [],
                    include_dirs = self.context.options.include_path,
                    post_include_lines = [],
                    libraries = [],
                    library_dirs = [],
                    separate_module_sources = [],
                    separate_module_files = [],
                )

        fields = self._make_struct_attr_list(attributes)
        setattr(CConfigure, str(name), configure.Struct("struct " + str(name), [(field[0], field[1]) for field in fields]))

        try:
            info = configure.configure(CConfigure)
        except:
            if len(fields) != 0:
                raise CompileError(u'Unable to find fields of struct from the C compiler. struct: %s; fields: %s' % (str(name), fields))
            else:
                return []
        
        return [(newField[0], newField[1], field[2]) for field, newField in zip(fields, info[str(name)]._fields_)]
    def _find_union_size(self, name):
        class CConfigure(object):
            _compilation_info_ = configure.ExternalCompilationInfo(
                    pre_include_lines = [],
                    includes = [self.include_file] if self.include_file else [],
                    include_dirs = self.context.options.include_path,
                    post_include_lines = [],
                    libraries = [],
                    library_dirs = [],
                    separate_module_sources = [],
                    separate_module_files = [],
                )
            union_t = configure.SizeOf(name)
            
        info = configure.configure(CConfigure)
        return info['union_t']
        
    def visit_CStructOrUnionDefNode(self, node):
        if node.kind == "struct":
            if self.isInExternScope:
                fields = self._make_ctypes_struct_union(node.name, node.attributes)
            else:
                fields = self._make_struct_attr_list(node.attributes)
                
            node.attributes = [(field[0], self._ctypeToStr(field[1], field[2])) for field in fields]
            return SingleAssignmentNode(0,
                                        lhs=NameNode(0, name=node.name),
                                        rhs=SimpleCallNode(0,
                                                           child_attrs=[],
                                                           function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_struct"),
                                                           args=[NameNode(0, name=u'['+','.join(['("%s", %s)' % field for field in node.attributes]) + ']')]))
        
        else:
            # Union definition
            fields = self._make_struct_attr_list(node.attributes)
            node.attributes = [(field[0], self._ctypeToStr(field[1], field[2])) for field in fields]
            args=[NameNode(0, name=u'['+','.join([u'("%s", %s)' % field for field in node.attributes]) + u']')]
            if self.isInExternScope:
                size = self._find_union_size(node.name)
                args += [NameNode(0, name=u'size=%d' % size)]
            return SingleAssignmentNode(0,
                                        lhs=NameNode(0, name=node.name),
                                        rhs=SimpleCallNode(0,
                                                           child_attrs=[],
                                                           function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_union"),
                                                           args=args))

    

    def visit_CDefExternNode(self, node):
        self.isInExternScope = True
        self.include_file = str(node.include_file)
        
        self.recurse_to_children(node)
        
        self.include_file = None
        self.isInExternScope = False
        
        tf = TreeFragment(u'with cython.ctypes_extern("%s"):\n  DUMMY' % str(node.include_file))
        
        extern_scope = tf.root.stats[0]
        extern_scope.body = node.body

        return extern_scope

    def _make_import_ctypes_node(self):
        return StatListNode(0, stats=[
            ImportNode(0, module_name=StringNode(0, value="cython"), name_list=[], level=0),
            ImportNode(0, module_name=StringNode(0, value="ctypes"), name_list=[], level=0),
            ])
        
    def visit_CTypeDefNode(self, node):
        decl = node.declarator
        _, type, type_name = self._cythonTypeToCtypes(node, decl)
        while isinstance(decl, CPtrDeclaratorNode):
            decl = decl.base
        name = decl.name
        
        args = [NameNode(0, name=type_name)]
        if self.isInExternScope:
            if type is not None:
                base_name = node.base_type.name + '*' * type_name.lower().count('pointer')
                tempType = self._get_actual_ctype(base_name, type)
                args = [NameNode(0, name=self._ctypeToStr(tempType))]
                
        return SingleAssignmentNode(0,
                                    lhs=NameNode(0, name=name),
                                    rhs=SimpleCallNode(0,
                                                       child_attrs=[],
                                                       function=AttributeNode(0, obj=NameNode(0, name=u"cython"), attribute=u"ctypes_typedef"),
                                                       args=args))
        
        
    def visit_ModuleNode(self, node):
        if hasattr(node.body, 'stats'):
            node.body.stats = [self._make_import_ctypes_node()] + node.body.stats
        else:
            node.body = StatListNode(0, stats=[self._make_import_ctypes_node(), node.body])
        self.recurse_to_children(node)
        return node
