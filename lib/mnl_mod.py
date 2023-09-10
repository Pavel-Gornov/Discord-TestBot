from lib import mnllib


class MnLFakeIOModule(mnllib.MnLBaseModule):
    def __init__(self):
        super().__init__()
        self.stdout = ""

        def fprint(*args, end='\n', sep=' '):
            self.stdout += sep.join([str(a) for a in args]) + end

        def finput(*args, **kwargs):
            return ''

        self.code_globals = {**self.code_globals,
                             'print': mnllib.PyMnLAdapter(self, fprint),
                             'input': mnllib.PyMnLAdapter(self, finput)}
