from enum import Enum


class TokenType(Enum):
    NONE = -1
    IDENTIFIER = 0
    LPAREN = 5
    RPAREN = 6
    NUMBER = 9
    STRING = 10
    COMMA = 12
    SEMICOLON = 13

class Token:
    def __init__(self, token_type: TokenType):
        self.type = token_type
        self.index = 0
        self.data = ""

    @property
    def as_int(self) -> int:
        return int(self.data)

    @property
    def as_str(self) -> str:
        return self.data

    def __repr__(self):
        return "Token[T:{}, {}]".format(self.type, self.data)


class Lexer:
    def __init__(self, buffer):
        self.splits = ",=();"
        self.whitespace = " \t\n\0"
        self.buffer = buffer
        self.tokens = []

    def push_token(self, token):
        token.index = len(self.tokens)
        self.tokens.append(self.identify_token(token))

    def lex(self):
        token = Token(TokenType.IDENTIFIER)
        token.data = ""
        in_str = False
        in_comment = False

        for ch in self.buffer:
            if ch == ';':
                in_comment = True

            if in_comment:
                if ch == '\n':
                    in_comment = False
                continue

            if ch == '"':
                in_str = not in_str

            if (ch in self.splits or ch in self.whitespace) and not in_str:
                if token.data != "":
                    self.push_token(token)
                    token = Token(TokenType.IDENTIFIER)

                if ch in self.splits:
                    split = Token(TokenType.IDENTIFIER)
                    split.data = ch
                    self.push_token(split)

                continue
            else:
                token.data += ch

        # if there is any data left in our token, push it
        if token.data != "":
            self.push_token(token)

        return

    def identify_token(self, token: Token) -> Token:
        data = token.data
        if data == ',':
            token.type = TokenType.COMMA
        elif data == '(':
            token.type = TokenType.LPAREN
        elif data == ')':
            token.type = TokenType.RPAREN
        elif data == ';':
            token.type = TokenType.SEMICOLON
        elif data[0] == '"' and data[-1] == '"':
            token.data = token.data[1:-1]
            token.type = TokenType.STRING
        elif data.isnumeric():
            token.type = TokenType.NUMBER
        # check for hexadecimal number
        elif data[0] == '0' and data[1] == 'x' and len(data) > 2:
            token.data = int(token.data, 16)
            token.type = TokenType.NUMBER
        else:
            token.type = TokenType.IDENTIFIER
        return token

    def print(self):
        for token in self.tokens:
            print("Token '{}' :: {}".format(token.data, token.type))

