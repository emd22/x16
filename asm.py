from enum import Enum, IntEnum
import typing

import getopt, sys

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
        self.splits = ",+-*/=();"
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
        symbols = '%'
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
        elif data[0] == '0' and data[1] == 'x' and len(data) > 2:
            token.data = str(int(token.data, 16)) # hack! convert our base 16 integer into a base 10 integer
            token.type = TokenType.NUMBER
        else:
            token.type = TokenType.IDENTIFIER
        return token

    def print(self):
        for token in self.tokens:
            print("Token '{}' :: {}".format(token.data, token.type))


class Macro:
    def __init__(self, name, arguments):
        self.name: str = name
        self.tokens: list[Token] = []
        self.arguments: int = arguments

    def call_macro(self, main_tokens: list[Token], arguments, token_index: int) -> list[Token]:
        tokens_to_remove: int = len(arguments) + len(arguments)

        for i in range(0, tokens_to_remove):
            main_tokens.pop(token_index)

        for idx, token in enumerate(self.tokens):
            if token.data[0] == '#':
                arg_index: int = int(token.data[1:])
                token = arguments[arg_index]

            main_tokens.insert(token_index + idx, token)

        return main_tokens


class Preproc:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.macros: list[Macro] = []


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

    def process_token(self):
        current_index = self.index
        token = self.next

        if token.data == '{#':
            name: str = self.eat(TokenType.IDENTIFIER).as_str
            args = self.eat(TokenType.NUMBER).as_int

            macro: Macro = Macro(name, args)

            while self.has_next:
                token: Token = self.next

                if token.type == TokenType.IDENTIFIER and token.as_str == '#}':
                    break

                macro.tokens.append(token)

            del self.tokens[current_index:self.index]
            self.index = current_index

            self.macros.append(macro)

    def find_macro(self, name: str) -> typing.Optional[Macro]:
        for macro in self.macros:
            if macro.name == name:
                return macro
        return None

    def run(self):
        while self.has_next:
            self.process_token()

class Register(IntEnum):

    NONE = 0
    X0 = 1
    X1 = 2
    X2 = 3
    X3 = 4
    SP = 5
    BP = 6
    PC = 7

    @staticmethod
    def get(ident: str) -> int:
        regmap = ['none', 'x0', 'x1', 'x2', 'x3', 'sp', 'bp', 'pc']

        for idx, val in enumerate(regmap):
            if val == ident:
                return idx

        return Register.NONE


class Label:
    def __init__(self, name, location):
        self.name = name
        self.location = location


class Opcode(IntEnum):
    NONE = 0x00
    BASE_PUSH = 0x01
    BASE_POP = 0x02
    BASE_ADD = 0x03
    SYS = 0x04
    BASE_BRANCH = 0x05
    BASE_COMPARE = 0x06
    BASE_AND = 0x07
    BASE_OR = 0x08
    BASE_NOT = 0x09

    PUSH = (BASE_PUSH << 4 | 0x00)
    PUSHI = (BASE_PUSH << 4 | 0x01)
    POP = (BASE_POP << 4 | 0x00)

    ADD = (BASE_ADD << 4 | 0x00)
    ADDI = (BASE_ADD << 4 | 0x01)

    BRANCH = (BASE_BRANCH << 4 | 0x00)
    BRANCH_LESS_THAN = (BASE_BRANCH << 4 | 0x01)
    BRANCH_GREATER_THAN = (BASE_BRANCH << 4 | 0x02)
    BRANCH_EQUAL_TO = (BASE_BRANCH << 4 | 0x03)
    BRANCH_NOT_EQUAL_TO = (BASE_BRANCH << 4 | 0x04)

    CMP  = ((BASE_COMPARE << 4) | 0x00)
    CMPI = ((BASE_COMPARE << 4) | 0x01)

    ANDI = ((BASE_AND << 4) | 0x01)
    ORI = ((BASE_OR << 4) | 0x01)

    NOT = ((BASE_NOT << 4) | 0x00)

class Instruction:
    def __init__(self, ident: str):
        self.ident = ident

    def parse(self, cg):
        pass

class IPush(Instruction):
    def parse(self, cg):
        cg.write(Opcode.PUSH.value)
        reg_ident = cg.eat(TokenType.IDENTIFIER).as_str
        # print(f'ident: {reg_ident} :: {Register.get(reg_ident)}')
        # write only our destination register
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))


class IPushi(Instruction):
    def parse(self, cg):
        cg.write(Opcode.PUSHI.value)


        value_token: Token = cg.tokens[cg.index]

        # write value passed to instruction
        if value_token.type == TokenType.IDENTIFIER:
            label_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
            cg.labels_to_update.append(Label(label_ident, len(cg.source)))

            # write a dummy value and update when the label is defined
            cg.write16(0x00)
        else:
            value: int = cg.eat(TokenType.NUMBER).as_int
            cg.write16(value)


class IPop(Instruction):
    def parse(self, cg):
        cg.write(Opcode.POP.value)
        reg_ident = cg.eat(TokenType.IDENTIFIER).as_str
        # write only our destination register
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))


class IAdd(Instruction):
    ADD = Opcode.ADD.value
    ADDI = Opcode.ADDI.value

    def __init__(self, ident, operation):
        super().__init__(ident)
        self.operation = operation

    def parse_immediate(self, cg):
        # write our immediate value
        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write16(value)
        cg.eat(TokenType.COMMA)
        # write our register value
        reg_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))


    def parse_register(self, cg):
        src_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.eat(TokenType.COMMA)
        # write our register value
        dest_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.get(src_ident), Register.get(dest_ident))

    def parse(self, cg):
        cg.write(self.operation)

        if self.operation == self.ADDI:
            self.parse_immediate(cg)
        else:
            self.parse_register(cg)


class ISys(Instruction):
    def parse(self, cg):
        cg.write(Opcode.SYS.value)
        # write value passed to instruction
        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write(value)
        pass


class IBranch(Instruction):
    DIRECT = Opcode.BRANCH.value
    LESS_THAN = Opcode.BRANCH_LESS_THAN.value
    GREATER_THAN = Opcode.BRANCH_GREATER_THAN.value
    EQUAL_TO = Opcode.BRANCH_EQUAL_TO.value
    NOT_EQUAL_TO = Opcode.BRANCH_NOT_EQUAL_TO.value

    def __init__(self, ident, operation):
        super().__init__(ident)
        self.operation = operation

    def parse(self, cg):
        cg.write(self.operation)

        label_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        # label = next(x for x in cg.labels if x.name == label_ident)
        cg.labels_to_update.append(Label(label_ident, len(cg.source)))

        # write a dummy value and update when the label is defined
        cg.write16(0x00)
        pass


class ICmp(Instruction):
    def parse(self, cg):
        cg.write(Opcode.CMP.value)

        src_reg: str = cg.eat(TokenType.IDENTIFIER).as_str

        cg.eat(TokenType.COMMA)
        # write our register value
        dest_reg: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.get(src_reg), Register.get(dest_reg))

        pass


class ICmpi(Instruction):
    def parse(self, cg):
        cg.write(Opcode.CMPI.value)

        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write16(value)

        cg.eat(TokenType.COMMA)
        # write our register value
        reg_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))
        pass


class INot(Instruction):
    def parse(self, cg):
        cg.write(Opcode.NOT.value)
        reg_ident = cg.eat(TokenType.IDENTIFIER).as_str
        # write only our destination register
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))


class IBitwiseI(Instruction):
    AND = Opcode.ANDI.value
    OR = Opcode.ORI.value

    def __init__(self, ident, operation):
        super().__init__(ident)
        self.operation = operation

    def parse(self, cg):
        cg.write(self.operation)

        value: int = cg.eat(TokenType.NUMBER).as_int
        cg.write16(value)

        cg.eat(TokenType.COMMA)
        # write our register value
        reg_ident: str = cg.eat(TokenType.IDENTIFIER).as_str
        cg.write_reg(Register.NONE.value, Register.get(reg_ident))
        pass


class CodeGen:
    instructions = [
        IPush('push'),
        IPushi('pushi'),
        IPop('pop'),
        IAdd('add', IAdd.ADD),
        IAdd('addi', IAdd.ADDI),
        ISys('sys'),
        ICmp('cmp'),
        ICmpi('cmpi'),
        IBranch('b', IBranch.DIRECT),
        IBranch('blt', IBranch.LESS_THAN),
        IBranch('bgt', IBranch.GREATER_THAN),
        IBranch('be', IBranch.EQUAL_TO),
        IBranch('bne', IBranch.NOT_EQUAL_TO),
        IBitwiseI('andi', IBitwiseI.AND),
        IBitwiseI('ori', IBitwiseI.OR),
        INot('not'),
    ]

    def __init__(self, tokens, preproc: Preproc, path):
        self.tokens = tokens
        self.preproc = preproc

        self.path = path

        self.index = 0
        self.source = []
        self.labels: list[Label] = []
        self.labels_to_update: list[Label] = []

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
            print(f'{self.path}: Error! unexpected token type {token.type} when expected {expected_type}')
            exit(1)
        return token

    def get_label_location(self, name) -> int:
        for label in self.labels:
            if label.name == name:
                return label.location
        return 0

    # go through each label and update the compiled references to the correct location
    def update_labels(self):
        for label in self.labels_to_update:
            value = self.get_label_location(label.name)
            self.source[label.location] = (value << 8) & 0xFF
            self.source[label.location + 1] = value & 0xFF
        pass


    def include_file(self, path):
        other_cg = process_source_file(path)
        self.preproc.macros.extend(other_cg.preproc.macros)
        self.tokens[self.index:self.index] = other_cg.tokens

    def parse_preproc(self, ident):
        ident_str = ident.as_str
        if ident_str == '.str':
            # get the string minus the quotes
            data = self.eat(TokenType.STRING).as_str[1:-1]
            # for each char, add the ascii value to our program
            for ch in data:
                self.source.append(ord(ch))
            # append the null terminator
            self.source.append(0)
        elif ident_str == '.include':
            path = self.eat(TokenType.STRING).as_str[1:-1]
            self.include_file(path)

    def parse_label(self, ident):
        label = Label(ident.as_str[:-1], len(self.source))
        self.labels.append(label)

    def parse_instr(self):
        ident: Token = self.eat(TokenType.IDENTIFIER)

        if ident.as_str[0] == '.':
            self.parse_preproc(ident)
            return

        if ident.as_str[-1] == ':':
            self.parse_label(ident)
            return

        for op in CodeGen.instructions:
            if op.ident == ident.data:
                op.parse(self)
                return

        macro: typing.Optional[Macro] = self.preproc.find_macro(ident.as_str)
        if macro is not None:
            token_index: int = self.index
            arguments = []

            for i in range(0, macro.arguments):
                arguments.append(self.next)
                if i < macro.arguments - 1:
                    self.eat(TokenType.COMMA)

            self.tokens = macro.call_macro(self.tokens, arguments, token_index - 1)
            self.index = token_index - 1

            self.parse_instr()
            return

        print(f'{self.path}: Error! Could not find instruction "{ident.as_str}"!')
        exit(1)

    def gen(self):
        while self.has_next:
            self.parse_instr()
        self.update_labels()

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


def process_source_file(path: str) -> CodeGen:
    source_file = open(path, 'r')
    lexer = Lexer(source_file.read())
    lexer.lex()

    preproc = Preproc(lexer.tokens)
    preproc.run()

    cg = CodeGen(preproc.tokens, preproc, path)
    cg.gen()

    return cg

def main():
    for i in range(1, len(sys.argv)):
        # path = 'demos/print/helloworld'
        path = sys.argv[i]
        print(f'Assembling {path}...')
        cg: CodeGen = process_source_file(path)

        # print(f'generated code: {cg.source}')

        cg.save(path.removesuffix('.dS') + '.bin')





if __name__ == "__main__":
    main()
