from lib.mnllib.modules import MnLBaseModule
from lib.mnllib.util import PyMnLAdapter


class MnLFakeIOModule(MnLBaseModule):
    def __init__(self):
        super().__init__()
        self.stdout = ""

        def fprint(*args, end='\n', sep=' '):
            self.stdout += sep.join([str(arg) for arg in args]) + end

        def finput(*args, **kwargs):
            return ''

        self.code_globals = {**self.code_globals,
                             'print': PyMnLAdapter(self, fprint),
                             'input': PyMnLAdapter(self, finput)}
