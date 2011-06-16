from Cython.CTypesBackend.ExternDefTransform import ExternDefTransform
from Cython.Compiler.ParseTreeTransforms import NormalizeTree
from Cython.TestUtils import TransformTest

class TestExternDefTransform(TransformTest):
    def test_func_transform(self):
        t = self.run_pipeline([NormalizeTree(self), ExternDefTransform(["c"])],
u"""\
cdef extern from "stdio.h":
    int printf(char *, int, int)\
""")
        self.assertEquals(self.codeToString(t),
"""\
import ctypes
printf = ctypes.CDLL(ctypes.util.find_library('c')).printf
printf.argtypes = [ctypes.POINTER(ctypes.c_char),ctypes.c_int,ctypes.c_int,]
printf.restype = ctypes.c_int\
""")

    def test_void_func_transform(self):
        t = self.run_pipeline([NormalizeTree(self), ExternDefTransform(["c"])],
u"""\
cdef extern from "stdio.h":
    void printf(char *, int, int)\
""")
        self.assertEquals(self.codeToString(t),
u"""\
import ctypes
printf = ctypes.CDLL(ctypes.util.find_library('c')).printf
printf.argtypes = [ctypes.POINTER(ctypes.c_char),ctypes.c_int,ctypes.c_int,]
printf.restype = None\
""")

    def test_struct_transform(self):
        # Probably platform dependent
        t = self.run_pipeline([NormalizeTree(self), ExternDefTransform(["c"])],
u"""\
cdef extern from "sys/time.h":
    ctypedef struct timeval:
        int tv_sec
        int tv_usec\
""")
        self.assertEquals(self.codeToString(t),
"""\
import ctypes
class timeval(ctypes.Structure,):
    pass
timeval._fields_ = [('tv_sec',ctypes.c_long,),('tv_usec',ctypes.c_long,),]\
""")

if __name__ == "__main__":
    import unittest
    unittest.main()
