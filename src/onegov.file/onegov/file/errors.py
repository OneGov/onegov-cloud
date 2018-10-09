class AlreadySignedError(RuntimeError):
    def __init__(self, file):
        super().__init__(f"File {file.id} has already been signed")


class InvalidTokenError(RuntimeError):
    def __init__(self, token):
        super().__init__(f"The given token could not be validated: {token}")


class TokenConfigurationError(RuntimeError):
    def __init__(self, token_type):
        super().__init__(f"Bad configuration of token type: {token_type}")
