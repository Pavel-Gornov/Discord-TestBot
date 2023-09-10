import regex as re
import textwrap
import pythonnet
import clr

clr.AddReference("System.Text.RegularExpressions")
from System.Text.RegularExpressions import Regex

class MnLParserError(Exception):
    def __init__(self, message, string):
        super().__init__(message)
        self.message = message
        self.string = string

class MnLExecutorError(Exception):
    def __init__(self, message, token, tokenid, exc):
        super().__init__(message)
        self.message = message
        self.token = token
        self.tokenid = tokenid
        self.exc = exc

class MnLSecurityError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.message = message
        self.code = code

_eval = eval
def eval(*args, **kwargs):
    if "__import__" in args[0]:
        raise MnLSecurityError("__import__ usages are restricted from evaluating", args[0])
    if "__builtins__" in args[0]:
        raise MnLSecurityError("__builtins__ usages are restricted from evaluating", args[0])
    #if "self" in args[0]:
    #    raise MnLSecurityError("self usages are restricted from evaluating", args[0])
    #print(args)
    return _eval(*args, **kwargs)

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
    def __str__(self): return self.__repr__()
    def __repr__(self): return f"func({self.arguments})"
        
class PyMnLAdapter():
    def __init__(self, executor, func):
        self.func = func
        self.executor = executor
    def __call__(self, *args, **kwargs):
        selfk, argsk, kwargsk = id(self), id(args), id(kwargs)
        return eval(f"s{selfk}.func(*a{argsk}, **a{kwargsk})", 
            {**self.executor.code_globals, "s"+str(selfk): self, "a"+str(argsk): args, "a"+str(kwargsk): kwargs},
            {})
    def __str__(self): return self.__repr__()
    def __repr__(self): return f"PythonCode(function={self.func})"

class MnLBaseModule():
    def __init__(self):
        self.code_globals = {}

class MnLImportedModule(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, val):
        self[attr] = val

class MnLExecutor():
    def __init__(self):
        self.code_globals = {'__builtins__': None, 'true': True, 'false': False, 'nil': None}
        self.code_locals = {}
        self.last_if_successful = False

    def reinit(self):
        return self.__init__()

    def load_module(self, module):
        self.code_globals = {**self.code_globals, **module.code_globals}

    def clean(self, token):
        if isinstance(token, list):
            return [self.clean(stoken) for stoken in token]
        return token.strip()

    def parse_method(self, toparse):
        return f"['{toparse.split('.')[0]}']"+("."+".".join(toparse.split(".")[1:]) if len(toparse.split(".")) > 1 else "")

    def tokenize(self, code):
        code = textwrap.dedent(code)
        type_regex = r"\w*"
        var_name_regex = r"\w+"
        value_regex = r".*"
        func_name_regex = r"[a-zA-Z0-9_.]+"
        #args_regex_1 = r"\((?:[^()]|(?R))*\)"
        #args_regex = r"\((?:[^)(]+|(?R))[\w\s]*\)"
        #code_regex_1 = r"\{(?:[^{}]|(?R))*\}"
        #code_regex = r"\{(?:[^}{]+|(?R))[\w\s]*\}"

        args_regex = r"\((?>\((?<c>)|[^()]+|\)(?<-c>))*(?(c)(?!))\)"
        code_regex = r"\{(?>\{(?<c>)|[^{}]+|\}(?<-c>))*(?(c)(?!))\}"

        set_regex = rf"({type_regex})\s*({var_name_regex})\s*=\s*({value_regex})"
        func_regex = rf"func\s+({func_name_regex})\s*({args_regex})\s*({code_regex})"
        if_regex = rf"if\s*({args_regex})\s*({code_regex})"
        elif_regex = rf"elseif\s*({args_regex})\s*({code_regex})"
        else_regex = rf"else\s*({code_regex})"
        while_regex = rf"while\s*({args_regex})\s*({code_regex})"
        call_regex = rf"({func_name_regex})\s*({args_regex})"
        return_regex = rf"return\s+({value_regex})"

        # List to store tokens
        tokens = []

        # Find and add matching constructs to the token list
        combined_regex = f"{func_regex}|{while_regex}|{if_regex}|{elif_regex}|{else_regex}|{call_regex}|{set_regex}|{return_regex}"
        #print(combined_regex)
        # Find all occurrences of the combined pattern using re.finditer()
        #matches = re.finditer(combined_regex, code, re.MULTILINE)
        matches = Regex.Matches(code, combined_regex)

        # Initialize a list to store the tokens
        tokens = []
        
        # Process each match and append the corresponding tokens to the 'tokens' list
        for match in matches:
            #print(match.Groups.Count)
            #print(" / ".join(str(g)+"-"+match.Groups[g].ToString() for g in range(match.Groups.Count)))
            #continue
            #print(match.groups())
            #for t in [f'{n+1} {i or "none"}' for n, i in enumerate(match.groups())]:
            #    print(f"{t}", end=" ")
            if match.Groups[1].ToString():
                tokens.append(["function", match.Groups[1].ToString(), match.Groups[2].ToString()[1:-1], self.tokenize(match.Groups[3].ToString()[1:-1])])
            elif match.Groups[4].ToString():
                tokens.append(["loop", "while", match.Groups[4].ToString()[1:-1], self.tokenize(match.Groups[5].ToString()[1:-1])])
            elif match.Groups[6].ToString():
                tokens.append(["statement", "if", match.Groups[6].ToString()[1:-1], self.tokenize(match.Groups[7].ToString()[1:-1])])
            elif match.Groups[8].ToString():
                tokens.append(["statement", "elseif", match.Groups[8].ToString()[1:-1], self.tokenize(match.Groups[9].ToString()[1:-1])])
            elif match.Groups[10].ToString():
                tokens.append(["statement", "else", self.tokenize(match.Groups[10].ToString()[1:-1])])
            elif match.Groups[11].ToString():
                tokens.append(["call", match.Groups[11].ToString(), match.Groups[12].ToString()[1:-1]])
            elif match.Groups[13].ToString():
                tokens.append(["set", match.Groups[13].ToString(), match.Groups[14].ToString(), match.Groups[15].ToString()])
            elif match.Groups[16].ToString():
                tokens.append(["return", match.Groups[16].ToString()])
            else:
                raise MnLParserError("Unknown token", match.group(0))

        tokens = self.clean(tokens)
        #print()
        return tokens

    def strparset(self, token):
        if token[0] == "set":
            return f"SET name '{token[2]}' type '{token[1]}' value {token[3]}"
        if token[0] == "statement":
            ret = ""
            if token[1] == "else":
                ret += f"STATEMENT type '{token[1]}' -> ("
                for stoken in token[2]:
                    ret += self.strparset(stoken) + " > "
                ret = ret[:-3] + ")"
                return ret
            ret += f"STATEMENT type '{token[1]}' on '{token[2]}' -> ("
            for stoken in token[2]:
                ret += self.strparset(stoken) + " > "
            ret = ret[:-3] + ")"
            return ret
        if token[0] == "loop":
            ret = ""
            ret += f"LOOP type '{token[1]}' on '{token[2]}' -> ("
            for stoken in token[3]:
                ret += self.strparset(stoken) + " > "
            ret = ret[:-3] + ")"
            return ret
        if token[0] == "function":
            ret = ""
            ret += f"FUNC name '{token[1]}' args '{token[2]}' -> ("
            for stoken in token[3]:
                ret += self.strparset(stoken) + " > "
            ret = ret[:-3] + ")"
            return ret
        if token[0] == "call":
            return f"CALL name '{token[1]}' args '{token[2]}'"
        if token[0] == "return":
            return +f"RETURN value {token[1]}"

    def strparse(self, token, indent):
        print("    "*indent, end="")
        if token[0] == "set":
            print(f"SET name '{token[2]}' type '{token[1]}' value {token[3]}")
        if token[0] == "statement":
            if token[1] == "else":
                print(f"STATEMENT type '{token[1]}'")
                for stoken in token[2]:
                    self.strparse(stoken, indent + 1)
                return
            print(f"STATEMENT type '{token[1]}' on '{token[2]}'")
            for stoken in token[3]:
                self.strparse(stoken, indent + 1)
        if token[0] == "loop":
            print(f"LOOP type '{token[1]}' on '{token[2]}'")
            for stoken in token[3]:
                self.strparse(stoken, indent + 1)
        if token[0] == "function":
            print(f"FUNC name '{token[1]}' args '{token[2]}'")
            for stoken in token[3]:
                self.strparse(stoken, indent + 1)
        if token[0] == "call":
            print(f"CALL name '{token[1]}' args '{token[2]}'")
        if token[0] == "return":
            print(f"RETURN value {token[1]}")

    def parse(self, token, level):
        #self.strparse(token, level)
        allowed_conv_types = ["int", "float", "str", "bool"]
        if not self.code_locals.get(level): self.code_locals[level] = {}
        if token[0] == "set":
            if level == 0 or self.code_globals.get(token[2]) is not None:
                self.code_globals[token[2]] = eval(f"{token[1]}({token[3]})" if token[1] in allowed_conv_types else f"{token[3]}", {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])
                return
            self.code_locals[level][token[2]] = eval(f"{token[1]}({token[3]})" if token[1] in allowed_conv_types else f"{token[3]}", {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])
        if token[0] == "statement":
            if token[1] == "else" and not self.last_if_successful:
                self.last_if_successful = False
                for stoken in token[2]:
                    self.parse(stoken, level + 1)
                return
            if token[1] == "else": return
            succeval = eval(token[2], self.code_globals, self.code_locals[level])
            if token[1] == "if":
                self.last_if_successful = False
                if succeval:
                    self.last_if_successful = True
                    for stoken in token[3]:
                        self.parse(stoken, level + 1)
                return
            if token[1] == "elseif" and not self.last_if_successful:
                self.last_if_successful = False
                if succeval:
                    self.last_if_successful = True
                    for stoken in token[3]:
                        self.parse(stoken, level + 1)
        if token[0] == "loop":
            #print(f"LOOP type '{token[1]}' on '{token[2]}'")
            while eval(token[2], self.code_globals, self.code_locals[level]):
                for stoken in token[3]:
                    self.parse(stoken, level + 1)
        if token[0] == "function":
            #print(f"FUNC name '{token[1]}' args '{token[2]}'")
            #for stoken in token[3]:
            #    self.parse(stoken, indent + 1)
            self.code_globals[token[1]] = MnLFunction(self, token[3], token[2])
        if token[0] == "call":
            selfk = id(self)
            eval(f"s{selfk}.code_globals{self.parse_method(token[1])}({token[2]})", {**self.code_globals, 's'+str(selfk): self}, self.code_locals[level])
            #print(f"CALL name '{token[1]}' args '{token[2]}'")
        if token[0] == "return":
            return eval(f"{token[1]}", {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])
            

    def run(self, code):
        comment_re = re.compile(r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?', re.DOTALL | re.MULTILINE)
        def __comment_replacer(match):
            start,mid,end = match.group(1,2,3)
            if mid is None: return ''
            elif start is not None or end is not None: return ''
            elif '\n' in mid: return '\n'
            else: return ' '
        code = comment_re.sub(__comment_replacer, code)

        tokens = self.tokenize(code)
        ret = None
        tokenid = 0
        curtoken = []
        try:
            for token in tokens:
                tokenid += 1
                curtoken = token
                ret = self.parse(token, 0)
                if ret: break
            return ret
        except Exception as e:
            if type(e) == MnLSecurityError: raise e
            #print(f"[E] Error when executing (tokenid {tokenid} / {curtoken}): {str(type(e))[8:-2]} - {e}")
            #print(f"[E] Core dump:\n[E]    {self.code_globals}\n[E]    {self.code_locals}")
            if (type(e) == TypeError and e.args[0] == "'NoneType' object is not subscriptable") or\
                (type(e) == KeyError) or (type(e) == NameError):
                raise MnLExecutorError("Accessing unset variable", token, tokenid, e)
            if type(e) == ZeroDivisionError:
                raise MnLExecutorError("Division by zero", token, tokenid, e)
            raise MnLExecutorError("Unknown executing error", token, tokenid, e)
            
    def strrun(self, code):
        comment_re = re.compile(r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?', re.DOTALL | re.MULTILINE)
        def __comment_replacer(match):
            start,mid,end = match.group(1,2,3)
            if mid is None: return ''
            elif start is not None or end is not None: return ''
            elif '\n' in mid: return '\n'
            else: return ' '
        code = comment_re.sub(__comment_replacer, code)

        tokens = self.tokenize(code)
        ret = None
        tokenid = 0
        curtoken = []
        for token in tokens:
            tokenid += 1
            curtoken = token
            self.strparse(token, 0)

class MnLIOModule(MnLBaseModule):
    def __init__(self):
        super().__init__()
        self.code_globals = {**self.code_globals,
        'print': PyMnLAdapter(self, print),
        'input': PyMnLAdapter(self, input)}

class MnLFileIOModule(MnLIOModule):
    def __init__(self):
        super().__init__()
        self.code_globals = {**self.code_globals,
        'open': PyMnLAdapter(self, open)}

modules = {'io': MnLIOModule, 'fileio': MnLFileIOModule}

class MnLAdvancedBaseModule(MnLBaseModule):
    def __init__(self):
        super().__init__()
        def import_caller(module):
            return __import__(module)
        def load_caller(module):
            return MnLImportedModule(modules[module]().code_globals)
        self.code_globals = {**self.code_globals,
        'require': PyMnLAdapter(self, import_caller),
        'require_module': PyMnLAdapter(self, load_caller)}