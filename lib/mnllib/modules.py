from . import util


class MnLBaseModule():
    def __init__(self):
        self.code_globals = {}


class MnLImportedModule(dict):
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, val):
        self[attr] = val


class MnLIOModule(MnLBaseModule):
    def __init__(self):
        super().__init__()
        self.code_globals = {**self.code_globals,
                             'print': util.PyMnLAdapter(self, print),
                             'input': util.PyMnLAdapter(self, input)}


class MnLFileIOModule(MnLIOModule):
    def __init__(self):
        super().__init__()
        self.code_globals = {**self.code_globals,
                             'open': util.PyMnLAdapter(self, open)}


__MODULES__ = {'io': MnLIOModule, 'file_io': MnLFileIOModule, 'base': MnLBaseModule}
