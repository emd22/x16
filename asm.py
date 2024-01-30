from enum import Enum, IntEnum


class TokenType(Enum):
    NONE = -1
    IDENTIFIER = 0
    OP_PLUS = 1
    OP_MINUS = 2
    OP_MUL = 3
    OP_DIV = 4
    LPAREN = 5
    RPAREN = 6
    LBRACE = 7
    RBRACE = 8
    NUMBER = 9
    STRING = 10
    SYMBOL = 11
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
        self.splits = ".,+-*/=(){};"
        self.ws = " \t\n\0"
        self.buffer = buffer
        self.tokens = []

    def push_token(self, token):
        token.index = len(self.tokens)
        self.tokens.append(self.ttoken(token))

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

            if (ch in self.splits or ch in self.ws) and not in_str:
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

    def ttoken(self, token: Token) -> Token:
        data = token.data
        symbols = '%#'
        if data == '+':
            token.type = TokenType.OP_PLUS
        elif data == ',':
            token.type = TokenType.COMMA
        elif data == '-':
            token.type = TokenType.OP_MINUS
        elif data == '*':
            token.type = TokenType.OP_MUL
        elif data == '/':
            token.type = TokenType.OP_DIV
        elif data == '(':
            token.type = TokenType.LPAREN
        elif data == ')':
            token.type = TokenType.RPAREN
        elif data == '{':
            token.type = TokenType.LBRACE
        elif data == '}':
            token.type = TokenType.RBRACE
        elif data == ';':
            token.type = TokenType.SEMICOLON
        elif data[0] == '"' and data[-1] == '"':
            token.type = TokenType.STRING
        elif data.isnumeric():
            token.type = TokenType.NUMBER
        elif data in symbols:
            token.type = TokenType.SYMBOL
        else:
            token.type = TokenType.IDENTIFIER
        return token

    def print(self):
        for token in self.tokens:
            print("Token '{}' :: {}".format(token.data, token.type))


class Instruction:
    def __init__(self, ident: str):
        self.ident = ident

    def parse(self, codegen):
        pass


class Register(IntEnum):

    NONE = 0
    X0 = 1
    X1 = 2
    X2 = 3
    X3 = 4
    SP = 5
    BP = 6
    PC = 7

    def get(ident: str) -> int:
        regmap = ['none', 'x0', 'x1', 'x2', 'x3', 'sp', 'bp', 'pc']

        for idx, val in enumerate(regmap):
            if val == ident:
                return idx

        return Register.NONE


class Opcode(IntEnum):
    NONE = 0x00
    BASE_PUSH = 0x01
    BASE_POP = 0x02
    BASE_ADD = 0x03
    SYS = 0x04

    PUSH = (BASE_PUSH << 4 | 0x00)
    PUSHI = (BASE_PUSH << 4 | 0x01)
    POP = (BASE_POP << 4 | 0x00)

    ADD = (BASE_ADD << 4 | 0x00)
    ADDI = (BASE_ADD << 4 | 0x01)


class IPushi(Instruction):
    def parse(self, cg):
        cg.write(Opcode.PUSHI.value)
        # write value passed to instruction
        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write16(value)
        pass

class IPop(Instruction):
    def parse(self, cg):
        cg.write(Opcode.POP.value)
        reg_ident = cg.eat(TokenType.IDENTIFIER).as_str
        # write only our destination register
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))

class IAddi(Instruction):
    def parse(self, cg):
        cg.write(Opcode.ADDI.value)
        # write our immediate value
        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write16(value)

        cg.eat(TokenType.COMMA)
        # write our register value
        reg_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))

class ISys(Instruction):
    def parse(self, cg):
        cg.write(Opcode.SYS.value)
        # write value passed to instruction
        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write(value)
        pass

class CodeGen:
    instructions = [
        IPushi('pushi'),
        IPop('pop'),
        IAddi('addi'),
        ISys('sys'),
    ]

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.source = []

    @property
    def next(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    @property
    def has_next(self) -> bool:
        return not self.index >= len(self.tokens)

    def eat(self, expected_type: TokenType):
        token: Token = self.next
        if token.type != expected_type:
            print(f'Error! unexpected token type {token.type} when expected {expected_type}')
            exit(1)
        return token

    def parse_instr(self):
        ident: Token = self.eat(TokenType.IDENTIFIER)
        for op in CodeGen.instructions:
            if op.ident == ident.data:
                op.parse(self)
                return
        print(f'Could not find instruction "{ident.as_str}"!')
        exit(1)
        pass

    def gen(self):
        while self.has_next:
            self.parse_instr()
        pass

    def write(self, value: int):
        self.source.append(value & 0xFF)

    def write16(self, value: int):
        self.write(value >> 8)
        self.write(value)

    def write_reg(self, src: int, dest: int):
        # top 4 bits is the source register, bottom 4 is destination
        self.write((src << 4) | (dest & 0x0F))

    def save(self, filename):
        output_file = open(filename, 'wb')
        output_file.write(bytes(self.source))
        output_file.close()


def main():
    source_file = open('demo.dS', 'r')
    lexer = Lexer(source_file.read())
    lexer.lex()

    print('Tokens:')
    lexer.print()

    cg = CodeGen(lexer.tokens)
    cg.gen()
    print(f'generated code: {cg.source}')

    cg.save('demo.bin')


if __name__ == "__main__":
    main()