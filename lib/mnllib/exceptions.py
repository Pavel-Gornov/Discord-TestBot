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
