class MnLFunction():
    def __init__(self, executor, code, arguments):
        self.code = code
        self.executor = executor
        self.arguments = [i.strip() for i in eval(str(arguments.split(",")))] if arguments != "" else []

    def __call__(self, *arguments):
        prep = [['set', '', argf, str(arg)] for argf, arg in zip(self.arguments, arguments)]
        ret = None
        for token in [*prep, *self.code]:
            ret = self.executor.parse(token, hash(self))
            if ret: return ret
        return 0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"func({self.arguments})"


class PyMnLAdapter():
    def __init__(self, executor, func):
        self.func = func
        self.executor = executor

    def __call__(self, *args, **kwargs):
        selfk, argsk, kwargsk = id(self), id(args), id(kwargs)
        return eval(f"s{selfk}.func(*a{argsk}, **a{kwargsk})",
                    {**self.executor.code_globals, "s" + str(selfk): self, "a" + str(argsk): args,
                     "a" + str(kwargsk): kwargs},
                    {})

    def __str__(self): return self.__repr__()

    def __repr__(self): return f"PythonCode(function={self.func})"
