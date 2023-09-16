import regex as re
import pythonnet
import clr
import textwrap

clr.AddReference("System.Text.RegularExpressions")
from System.Text.RegularExpressions import Regex

from . import exceptions
from . import util
from . import modules

version = "2.0"


class MnLEngine():
    def __init__(self):
        self.code_globals = {'__builtins__': None, 'true': True, 'false': False, 'nil': None}
        self.allow_using = False
        self.using_try_module = False
        self.using_try_python = False
        self.using_module_blacklist = []
        self.using_python_blacklist = []
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
        return f"['{toparse.split('.')[0]}']" + (
            "." + ".".join(toparse.split(".")[1:]) if len(toparse.split(".")) > 1 else "")

    def tokenize(self, code):
        code = textwrap.dedent(code)
        type_regex = r"\w*"
        var_name_regex = r"\w+"
        value_regex = r".*"
        func_name_regex = r"[a-zA-Z0-9_.]+"
        # args_regex_1 = r"\((?:[^()]|(?R))*\)"
        # args_regex = r"\((?:[^)(]+|(?R))[\w\s]*\)"
        # code_regex_1 = r"\{(?:[^{}]|(?R))*\}"
        # code_regex = r"\{(?:[^}{]+|(?R))[\w\s]*\}"

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
        using_regex = rf"using\s*<\s*({value_regex}).mnl\s*>"
        using_as_regex = rf"using\s*<\s*({value_regex}).mnl\s*>\s*as\s+({value_regex})"

        # List to store tokens
        tokens = []

        # Find and add matching constructs to the token list
        combined_regex = f"{func_regex}|{while_regex}|{if_regex}|{elif_regex}|{else_regex}|{call_regex}|{set_regex}|{return_regex}|{using_as_regex}|{using_regex}"
        # print(combined_regex)
        # Find all occurrences of the combined pattern using re.finditer()
        # matches = re.finditer(combined_regex, code, re.MULTILINE)

        comment_re = re.compile(r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?', re.DOTALL | re.MULTILINE)

        def __comment_replacer(match):
            start, mid, end = match.group(1, 2, 3)
            if mid is None:
                return ''
            elif start is not None or end is not None:
                return ''
            elif '\n' in mid:
                return '\n'
            else:
                return ' '

        code = comment_re.sub(__comment_replacer, code)

        matches = Regex.Matches(code, combined_regex)

        # Initialize a list to store the tokens
        tokens = []

        # Process each match and append the corresponding tokens to the 'tokens' list
        for match in matches:
            # print(match.Groups.Count)
            # print(" / ".join(str(g)+"-"+match.Groups[g].ToString() for g in range(match.Groups.Count)))
            # continue
            # print(match.groups())
            # for t in [f'{n+1} {i or "none"}' for n, i in enumerate(match.groups())]:
            #    print(f"{t}", end=" ")
            if match.Groups[1].ToString():
                tokens.append(["function", match.Groups[1].ToString(), match.Groups[2].ToString()[1:-1],
                               self.tokenize(match.Groups[3].ToString()[1:-1])])
            elif match.Groups[4].ToString():
                tokens.append(["loop", "while", match.Groups[4].ToString()[1:-1],
                               self.tokenize(match.Groups[5].ToString()[1:-1])])
            elif match.Groups[6].ToString():
                tokens.append(["statement", "if", match.Groups[6].ToString()[1:-1],
                               self.tokenize(match.Groups[7].ToString()[1:-1])])
            elif match.Groups[8].ToString():
                tokens.append(["statement", "elseif", match.Groups[8].ToString()[1:-1],
                               self.tokenize(match.Groups[9].ToString()[1:-1])])
            elif match.Groups[10].ToString():
                tokens.append(["statement", "else", self.tokenize(match.Groups[10].ToString()[1:-1])])
            elif match.Groups[11].ToString():
                tokens.append(["call", match.Groups[11].ToString(), match.Groups[12].ToString()[1:-1]])
            elif match.Groups[13].ToString():
                tokens.append(
                    ["set", match.Groups[13].ToString(), match.Groups[14].ToString(), match.Groups[15].ToString()])
            elif match.Groups[16].ToString():
                tokens.append(["return", match.Groups[16].ToString()])
            elif match.Groups[17].ToString():
                tokens.append(["using", match.Groups[17].ToString(), match.Groups[18].ToString()])
            elif match.Groups[19].ToString():
                tokens.append(["using", match.Groups[19].ToString(), match.Groups[19].ToString()])
            else:
                raise exceptions.MnLParserError("Unknown token", match.Groups[0].ToString())

        tokens = self.clean(tokens)
        # print()
        return tokens

    def strparset(self, token):
        if token[0] == "using":
            return f"USING lib '{token[1]}' name '{token[2]}'\n"
        if token[0] == "set":
            return f"SET name '{token[2]}'" + (
                ' type \'' + token[1] + '\'' if len(token[1]) > 0 else '') + f" value '{token[3]}'\n"
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
            ret += f"FUNC name '{token[1]}'" + (' args \'' + token[2] + '\'' if len(token[2]) > 0 else '') + " -> ("
            for stoken in token[3]:
                ret += self.strparset(stoken) + " > "
            ret = ret[:-3] + ")"
            return ret
        if token[0] == "call":
            return f"CALL name {token[1]}" + (' args \'' + token[2] + '\'' if len(token[2]) > 0 else '') + "\n"
        if token[0] == "return":
            return +f"RETURN value {token[1]}"

    def strparse(self, token, indent):
        ret = ""
        ret += "    " * indent
        if token[0] == "using":
            ret += f"USING lib '{token[1]}' name '{token[2]}'\n"
        if token[0] == "set":
            ret += f"SET name '{token[2]}'" + (
                ' type \'' + token[1] + '\'' if len(token[1]) > 0 else '') + f" value '{token[3]}'\n"
        if token[0] == "statement":
            if token[1] == "else":
                ret += f"STATEMENT type '{token[1]}'\n"
                for stoken in token[2]:
                    ret += self.strparse(stoken, indent + 1)
                return ret
            ret += f"STATEMENT type '{token[1]}' on condition '{token[2]}'\n"
            for stoken in token[3]:
                ret += self.strparse(stoken, indent + 1)
        if token[0] == "loop":
            ret += f"LOOP type '{token[1]}' on condition '{token[2]}'\n"
            for stoken in token[3]:
                ret += self.strparse(stoken, indent + 1)
        if token[0] == "function":
            ret += f"FUNC name '{token[1]}" + (' args \'' + token[2] + '\'' if len(token[2]) > 0 else '') + "\n"
            for stoken in token[3]:
                ret += self.strparse(stoken, indent + 1)
        if token[0] == "call":
            ret += f"CALL name {token[1]}" + (' args \'' + token[2] + '\'' if len(token[2]) > 0 else '') + "\n"
        if token[0] == "return":
            ret += f"RETURN value {token[1]}"
        return ret

    def parse(self, token, level):
        # self.strparse(token, level)
        allowed_conv_types = ["int", "float", "str", "bool"]
        if not self.code_locals.get(level): self.code_locals[level] = {}
        if token[0] == "set":
            if level == 0 or self.code_globals.get(token[2]) is not None:
                self.code_globals[token[2]] = eval(
                    f"{token[1]}({token[3]})" if token[1] in allowed_conv_types else f"{token[3]}",
                    {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])
                return
            self.code_locals[level][token[2]] = eval(
                f"{token[1]}({token[3]})" if token[1] in allowed_conv_types else f"{token[3]}",
                {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])
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
            while eval(token[2], self.code_globals, self.code_locals[level]):
                for stoken in token[3]:
                    self.parse(stoken, level + 1)
        if token[0] == "function":
            self.code_globals[token[1]] = util.MnLFunction(self, token[3], token[2])
        if token[0] == "using":
            if not self.allow_using: raise exceptions.MnLExecutorError(
                "Directive 'using' is not allowed in this context", token, -1, None)
            lib = None
            if not lib and self.using_try_module and not token[1] in self.using_module_blacklist:
                try:
                    lib = modules.MnLImportedModule(modules.__MODULES__[token[1]]().code_globals)
                except:
                    pass
            if not lib and self.using_try_python and not token[1] in self.using_python_blacklist:
                try:
                    lib = __import__(token[1])
                except:
                    pass

            self.code_globals = {**self.code_globals, token[2]: lib}
        if token[0] == "call":
            selfk = id(self)
            eval(f"s{selfk}.code_globals{self.parse_method(token[1])}({token[2]})",
                 {**self.code_globals, 's' + str(selfk): self}, self.code_locals[level])
        if token[0] == "return":
            return eval(f"{token[1]}", {**self.code_globals, '__builtins__': __builtins__}, self.code_locals[level])

    def run(self, code):
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
            if type(e) == exceptions.MnLSecurityError: raise e
            # print(f"[E] Error when executing (tokenid {tokenid} / {curtoken}): {str(type(e))[8:-2]} - {e}")
            # print(f"[E] Core dump:\n[E]    {self.code_globals}\n[E]    {self.code_locals}")
            if (type(e) == TypeError and e.args[0] == "'NoneType' object is not subscriptable") or \
                    (type(e) == KeyError) or (type(e) == NameError):
                raise exceptions.MnLExecutorError("Accessing unset variable", token, tokenid, e)
            if type(e) == ZeroDivisionError:
                raise exceptions.MnLExecutorError("Division by zero", token, tokenid, e)
            raise exceptions.MnLExecutorError("Unknown executing error", token, tokenid, e)

    def strrun(self, code):
        tokens = self.tokenize(code)
        ret = None
        tokenid = 0
        curtoken = []
        for token in tokens:
            tokenid += 1
            curtoken = token
            print(self.strparse(token, 0), end="")

    def __str__(self=None):
        return "MnLEngine_v2"
