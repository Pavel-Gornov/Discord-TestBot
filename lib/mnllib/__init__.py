from . import engine_v1
from . import engine_v2
from . import exceptions
from . import util
from . import modules

__VERSION__ = "v1.2a"
__ENGINES__ = {'1.0': engine_v1.MnLEngine, '2.0': engine_v2.MnLEngine, 'default': engine_v2.MnLEngine}
__MODULES__ = modules.__MODULES__

_eval = eval


def eval(*args, **kwargs):
    if "__import__" in args[0]:
        raise exceptions.MnLSecurityError("__import__ usages are restricted from evaluating", args[0])
    if "__builtins__" in args[0]:
        raise exceptions.MnLSecurityError("__builtins__ usages are restricted from evaluating", args[0])
    # if "self" in args[0]:
    #    raise MnLSecurityError("self usages are restricted from evaluating", args[0])
    # print(args)
    return _eval(*args, **kwargs)

