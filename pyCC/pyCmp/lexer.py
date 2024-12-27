"""
    Modified by DrkWithT (Derek Tan) at 12/20/2024:
    Refactor lexer to recognize more tokens flexibly.
"""

from enum import Enum, auto

## Types & Aliases ##

OPERATOR_SYMBOLS = '+-*/!=&|<>'

class TokenType(Enum):
    SPACING = auto()
    LINE_COMMENT = auto()
    IDENTIFIER = auto()
    KEYWORD = auto()
    LITERAL_CHAR = auto()
    LITERAL_INT = auto()
    TYPENAME_CHAR = auto()
    TYPENAME_INT = auto()
    TYPENAME_VOID = auto()
    OP_ASSIGN = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_TIMES = auto()
    OP_SLASH = auto()
    OP_LT_SIGN = auto()
    OP_LTE_SIGN = auto()
    OP_GT_SIGN = auto()
    OP_GTE_SIGN = auto()
    OP_TWO_EQU = auto()
    OP_BANG_EQU = auto()
    OP_LOGIC_AND = auto()
    OP_LOGIC_OR = auto()
    COMMA = auto()
    SEMICOLON = auto()
    PAREN_OPEN = auto()
    PAREN_CLOSE = auto()
    BRACE_OPEN = auto()
    BRACE_CLOSE = auto()
    UNKNOWN = auto()

# NOTE represents a hashmap of reserved words in C to lexical type.
LexemeTable = dict[str, TokenType]

# NOTE represents a line,col pair.
TokenPos = tuple[int, int]

# NOTE represents a token containing a lexeme, type, and position... None means EOF!
TokenObj = tuple[str, TokenPos, TokenType] | None

## Constants ##

PYCC_KEYWORDS = {
    "return": TokenType.KEYWORD,
    "if": TokenType.KEYWORD,
    "else": TokenType.KEYWORD,
    "while": TokenType.KEYWORD,
    "break": TokenType.KEYWORD,
    "continue": TokenType.KEYWORD
}

PYCC_TYPENAMES = {
    "char": TokenType.TYPENAME_CHAR,
    "int": TokenType.TYPENAME_INT,
    "void": TokenType.TYPENAME_VOID
}

PYCC_OPERATORS = {
    "=": TokenType.OP_ASSIGN,
    "+": TokenType.OP_PLUS,
    "-": TokenType.OP_MINUS,
    "*": TokenType.OP_TIMES,
    "/": TokenType.OP_SLASH,
    "<": TokenType.OP_LT_SIGN,
    "<=": TokenType.OP_LTE_SIGN,
    ">": TokenType.OP_GT_SIGN,
    ">=": TokenType.OP_GTE_SIGN,
    "==": TokenType.OP_TWO_EQU,
    "!=": TokenType.OP_BANG_EQU,
    "&&": TokenType.OP_LOGIC_AND,
    "||": TokenType.OP_LOGIC_OR
}

## Helper Functions ##

def match_spacing(symbol: str) -> bool:
    return symbol[0].isspace()

def match_alphabetic(symbol: str) -> bool:
    return symbol[0].isalpha() or symbol[0] == '_'

def match_numeric(symbol: str) -> bool:
    return symbol[0].isnumeric()

def match_op_symbol(symbol: str) -> bool:
    return OPERATOR_SYMBOLS.find(symbol[0]) != -1

class Lexer:
    """
        A tokenizer for a tiny part of C99?? O_O
    """
    def __init__(self, keywords: LexemeTable = PYCC_KEYWORDS, typenames: LexemeTable = PYCC_TYPENAMES, operators: LexemeTable = PYCC_OPERATORS) -> None:
        self.keyword_table = keywords
        self.types_table = typenames
        self.operator_table = operators
        self.source_view: str = None
        self.token_hops: list[int] = []
        self.pos: int = 0
        self.limit: int = 0
        self.line: int = 1;
        self.column: int = 1;

    def use_source(self, source: str):
        self.source_view = source
        self.pos = 0
        self.limit = len(source)
        self.line = 1
        self.column = 1

    def record_hop(self, hop_span: int):
        self.token_hops.append(hop_span)

    def unwind_hop(self):
        hop_n = len(self.token_hops)

        if hop_n == 0:
            return

        self.pos -= self.token_hops[hop_n - 1]
        self.token_hops.pop()

    def update_tracked_loc(self, symbol: str) -> None:
        if symbol[0] == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1

    def at_end(self) -> bool:
        return self.pos >= self.limit

    def lex_spacing(self) -> TokenObj:
        token_start = self.pos
        token_length = 0

        while not self.at_end():
            c = self.source_view[self.pos]

            if not match_spacing(c):
                break

            self.update_tracked_loc(c)
            self.pos += 1
            token_length += 1

        self.record_hop(token_length)

        return (
            self.source_view[token_start: token_start + token_length],
            (self.line, self.column),
            TokenType.SPACING
        )

    def lex_comment(self) -> TokenObj:
        self.pos += 2 # skip '//'
        token_start = self.pos
        token_length = 0

        while not self.at_end():
            c = self.source_view[self.pos]

            if c == '\n':
                break

            self.update_tracked_loc(c)
            self.pos += 1
            token_length += 1

        self.record_hop(token_length + 2)

        return (
            self.source_view[token_start: token_start + token_length],
            (self.line, self.column - token_length),
            TokenType.LINE_COMMENT
        )

    def lex_single(self, token_type: TokenType) -> TokenObj:
        token_start = self.pos
        self.pos += 1
        self.update_tracked_loc(self.source_view[self.pos - 1])

        self.record_hop(1)

        return (
            self.source_view[token_start: token_start + 1],
            (self.line, self.column - 1),
            token_type
        )

    def lex_char(self) -> TokenObj:
        self.update_tracked_loc(self.source_view[self.pos])
        self.pos += 1

        token_start = self.pos
        self.update_tracked_loc(self.source_view[self.pos])
        self.pos += 1

        maybe_closing_quote = self.source_view[self.pos]
        self.update_tracked_loc(maybe_closing_quote)
        self.pos += 1

        self.record_hop(3)

        if maybe_closing_quote != '\'':
            return ('\0', (self.line, self.column - 3), TokenType.UNKNOWN)

        return (
            self.source_view[token_start: token_start + 1],
            (self.line, self.column - 3),
            TokenType.LITERAL_CHAR
        )

    def lex_word(self) -> TokenObj:
        token_start = self.pos
        token_length = 0

        while not self.at_end():
            c = self.source_view[self.pos]

            if not match_alphabetic(c):
                break

            self.update_tracked_loc(c)
            self.pos += 1
            token_length += 1

        self.record_hop(token_length)

        lexeme = self.source_view[token_start: token_start + token_length]
        token_type = TokenType.UNKNOWN

        if self.keyword_table.get(lexeme) is not None:
            token_type = self.keyword_table.get(lexeme)
        elif self.types_table.get(lexeme) is not None:
            token_type = self.types_table.get(lexeme)
        else:
            token_type = TokenType.IDENTIFIER

        return (
            lexeme,
            (self.line, self.column - token_length),
            token_type
        )
    
    def lex_number(self) -> TokenObj:
        token_start = self.pos
        token_length = 0
        dots = 0

        while not self.at_end():
            c = self.source_view[self.pos]

            if not match_numeric(c):
                break

            self.update_tracked_loc(c)

            if c == '.':
                dots += 1

            self.pos += 1
            token_length += 1

        self.record_hop(token_length)

        return (
            self.source_view[token_start: token_start + token_length],
            (self.line, self.column - token_length),
            TokenType.LITERAL_INT
        )

    def lex_operator(self) -> TokenObj:
        token_start = self.pos
        token_length = 0

        while not self.at_end():
            c = self.source_view[self.pos]

            if not match_op_symbol(c):
                break

            self.update_tracked_loc(c)
            self.pos += 1
            token_length += 1

        self.record_hop(token_length)

        lexeme = self.source_view[token_start: token_start + token_length]

        if self.operator_table.get(lexeme) is None:
            return (
                lexeme,
                (self.line, self.column - token_length),
                TokenType.UNKNOWN
            )

        return (
            lexeme,
            (self.line, self.column),
            self.operator_table.get(lexeme)
        )

    def lex_next(self) -> TokenObj:
        if self.at_end():
            return None

        peeked_c = self.source_view[self.pos]

        if peeked_c == ',':
            return self.lex_single(TokenType.COMMA)
        elif peeked_c == ';':
            return self.lex_single(TokenType.SEMICOLON)
        elif peeked_c == '(':
            return self.lex_single(TokenType.PAREN_OPEN)
        elif peeked_c == ')':
            return self.lex_single(TokenType.PAREN_CLOSE)
        elif peeked_c == '{':
            return self.lex_single(TokenType.BRACE_OPEN)
        elif peeked_c == '}':
            return self.lex_single(TokenType.BRACE_CLOSE)
        elif peeked_c == '/' and self.source_view[self.pos + 1] == '/':
            return self.lex_comment()
        elif peeked_c == '\'':
            return self.lex_char()

        if match_spacing(peeked_c):
            return self.lex_spacing()
        elif match_alphabetic(peeked_c):
            return self.lex_word()
        elif match_numeric(peeked_c):
            return self.lex_number()
        elif match_op_symbol(peeked_c):
            return self.lex_operator()

        self.pos += 1
        self.record_hop(1)
        self.update_tracked_loc(peeked_c)

        return (
            peeked_c,
            (self.line, self.column - 1),
            TokenType.UNKNOWN
        )
