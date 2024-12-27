"""
    parser.py\n
    Modified by DrkWithT (Derek Tan) on 12/20/2024\n
    NOTE this will need a type-qualifier & type name parse function.
"""

from enum import Enum, auto
import pyCC.pyCmp.lexer as lex
import pyCC.pyCmp.ast_nodes as ast

## Aliases & Types & Constants ##

ParseResult = tuple[bool, list[ast.Stmt]]
TokenTag = lex.TokenType
TokenTags = list[TokenTag]

class TokenChoice(Enum):
    previous = auto()
    current = auto()

TYPENAME_TABLE = {
    "void": ast.DataType.VOID,
    "char": ast.DataType.CHAR,
    "int": ast.DataType.INT
}

class Parser:
    def __init__(self):
        self.lexer = lex.Lexer()
        self.curr: lex.TokenObj = None
        self.prev: lex.TokenObj = None
        self.error_count = 0
        self.passed_space = False

    def at_end(self) -> bool:
        return self.curr is None

    def peek_curr(self) -> lex.TokenObj:
        return self.curr

    def peek_prev(self) -> lex.TokenObj:
        return self.prev

    def advance(self) -> lex.TokenObj:
        self.passed_space = False
        temp = None

        while True:
            temp = self.lexer.lex_next()

            # NOTE handle the EOF!
            if temp is None:
                break

            if temp[2] == lex.TokenType.SPACING or temp[2] == lex.TokenType.LINE_COMMENT:
                if temp[2] == lex.TokenType.SPACING:
                    self.passed_space = True
                continue

            break

        return temp

    def match_token(self, choice: TokenChoice, matches: TokenTags) -> bool:
        if len(matches) == 0:
            return True

        if choice == TokenChoice.current:
            for m in matches:
                if self.curr[2] == m:
                    return True

            return False
        else:
            for m in matches:
                if self.curr[2] == m:
                    return True

            return False

    def consume_token(self, matches: TokenTags):
        if self.match_token(TokenChoice.current, matches):
            self.prev = self.curr
            self.curr = self.advance()
            return
        elif self.match_token(TokenChoice.current, [lex.TokenType.UNKNOWN]):
            raise SyntaxError('Invalid token!')

        raise SyntaxError('Unexpected token!')

    def use_source(self, source: str):
        self.lexer.use_source(source)
        self.curr: lex.TokenObj = None
        self.prev: lex.TokenObj = None
        self.error_count = 0

    def parse_literal(self) -> ast.Expr:
        if self.match_token(TokenChoice.current, [TokenTag.LITERAL_CHAR]):
            temp = self.peek_curr()
            self.consume_token([])
            return ast.Literal((temp, None), ast.DataType.CHAR)
        elif self.match_token(TokenChoice.current, [TokenTag.LITERAL_INT]):
            temp = self.peek_curr()
            self.consume_token([])
            return ast.Literal((temp, None), ast.DataType.INT)
        elif self.match_token(TokenChoice.current, [TokenTag.PAREN_OPEN]):
            self.consume_token([])
            temp = self.parse_expr()
            self.consume_token([TokenTag.PAREN_CLOSE])
            return temp
        elif self.match_token(TokenChoice.current, [TokenTag.IDENTIFIER]):
            return self.parse_call_or_name()

        raise SyntaxError('Invalid token for literal!')

    def parse_call_or_name(self):
        self.consume_token([])
        temp_name_token = self.peek_prev()

        if self.match_token(TokenChoice.current, [TokenTag.PAREN_OPEN]):
            return ast.Call(temp_name_token[0], self.parse_args())

        return ast.Literal((temp_name_token, None), ast.DataType.UNKNOWN)

    def parse_unary(self) -> ast.Expr:
        if self.match_token(TokenChoice.current, [TokenTag.OP_MINUS]):
            self.consume_token([])
            return ast.Unary(self.parse_literal(), ast.OpType.OP_NEG)

        return self.parse_literal()

    def parse_factor(self) -> ast.Expr:
        lhs = self.parse_unary()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_TIMES, TokenTag.OP_SLASH]):
                break

            temp_op = ast.OpType.OP_DIV

            if self.peek_curr()[2] == TokenTag.OP_TIMES:
                temp_op = ast.OpType.OP_MULT

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_unary(), temp_op)

        return lhs

    def parse_term(self) -> ast.Expr:
        lhs = self.parse_factor()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_PLUS, TokenTag.OP_MINUS]):
                break

            temp_op = ast.OpType.OP_SUB

            if self.peek_curr()[2] == TokenTag.OP_PLUS:
                temp_op = ast.OpType.OP_ADD

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_factor(), temp_op)

        return lhs

    def parse_comparison(self) -> ast.Expr:
        lhs = self.parse_term()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_LT_SIGN, TokenTag.OP_LTE_SIGN, TokenTag.OP_GT_SIGN, TokenTag.OP_GTE_SIGN]):
                break

            temp_op = ast.OpType.OP_NONE
            temp_tag = self.peek_curr()[2]

            if temp_tag == TokenTag.OP_LT_SIGN:
                temp_op = ast.OpType.OP_LT
            elif temp_tag == TokenTag.OP_LTE_SIGN:
                temp_op = ast.OpType.OP_LTE
            elif temp_tag == TokenTag.OP_GT_SIGN:
                temp_op = ast.OpType.OP_GT
            elif temp_tag == TokenTag.OP_GTE_SIGN:
                temp_op = ast.OpType.OP_GTE

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_term(), temp_op)

        return lhs

    def parse_equality(self) -> ast.Expr:
        lhs = self.parse_comparison()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_TWO_EQU, TokenTag.OP_BANG_EQU]):
                break

            temp_op = ast.OpType.OP_INEQUALITY

            if self.peek_curr()[2] == TokenTag.OP_TWO_EQU:
                temp_op = ast.OpType.OP_EQUALITY

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_comparison(), temp_op)

        return lhs

    def parse_and(self) -> ast.Expr:
        lhs = self.parse_equality()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_LOGIC_AND]):
                break

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_equality(), ast.OpType.OP_LOGIC_AND)

        return lhs

    def parse_or(self) -> ast.Expr:
        lhs = self.parse_and()

        while not self.at_end():
            if not self.match_token(TokenChoice.current, [TokenTag.OP_LOGIC_OR]):
                break

            self.consume_token([])

            lhs = ast.Binary(lhs, self.parse_and(), ast.OpType.OP_LOGIC_OR)

        return lhs
    
    def parse_expr(self) -> ast.Expr:
        if self.match_token(TokenChoice.current, [TokenTag.IDENTIFIER]):
            self.consume_token([])
            prev_name_token = self.prev

            # NOTE my workaround: now check an operator... if '=', we're at assign, but otherwise the equivalent <or> rule applies.
            if self.match_token(TokenChoice.current, [TokenTag.OP_ASSIGN]):
                self.consume_token([])
                return ast.Binary(ast.Literal((prev_name_token, None), ast.OpType.OP_NONE), self.parse_expr(), ast.OpType.OP_ASSIGN)

            # NOTE Weird fix: backtrack to prepare for parsing a name-started expression!
            self.lexer.unwind_hop()
            self.lexer.unwind_hop()
            self.lexer.unwind_hop()
            self.consume_token([])

            return self.parse_or()

        return self.parse_or()

    def parse_declaration(self) -> ast.Stmt:
        self.consume_token([TokenTag.TYPENAME_VOID, TokenTag.TYPENAME_CHAR, TokenTag.TYPENAME_INT])

        temp_typename = TYPENAME_TABLE.get(self.peek_prev()[0])
        temp_name = self.peek_curr()[0]

        self.consume_token([TokenTag.IDENTIFIER])

        if self.match_token(TokenChoice.current, [TokenTag.OP_ASSIGN]):
            self.consume_token([])
            temp_rhs = self.parse_expr()
            self.consume_token([TokenTag.SEMICOLON])

            return ast.Variable(temp_name, temp_typename, temp_rhs)
        elif self.match_token(TokenChoice.current, [TokenTag.PAREN_OPEN]):
            temp_func_params = self.parse_params()
            temp_func_body = self.parse_block()

            return ast.FunctionDecl(temp_name, temp_typename, temp_func_params, temp_func_body)
        
        raise SyntaxError('Invalid token for declaration!')

    def parse_variable(self) -> ast.Stmt:
        self.consume_token([TokenTag.TYPENAME_VOID, TokenTag.TYPENAME_CHAR, TokenTag.TYPENAME_INT])

        temp_typename = TYPENAME_TABLE.get(self.peek_prev()[0]) or ast.DataType.UNKNOWN
        temp_name = self.peek_curr()[0]

        self.consume_token([TokenTag.IDENTIFIER])
        self.consume_token([TokenTag.OP_ASSIGN])

        temp_rhs = self.parse_expr()
        self.consume_token([TokenTag.SEMICOLON])

        return ast.Variable(temp_name, temp_typename, temp_rhs)

    def parse_block(self) -> ast.Stmt:
        self.consume_token([TokenTag.BRACE_OPEN])

        temp_stmts = []

        while not self.at_end():
            if self.peek_curr() is None:
                raise SyntaxError('Missing closing brace for block.')

            if self.match_token(TokenChoice.current, [TokenTag.BRACE_CLOSE]):
                self.consume_token([])
                break

            temp_stmts.append(self.parse_nested_stmt())

        return ast.Block(temp_stmts)

    def parse_nested_stmt(self) -> ast.Stmt:
        temp_lexeme = self.peek_curr()[0]

        if self.match_token(TokenChoice.current, [TokenTag.KEYWORD])  and temp_lexeme == 'if':
            return self.parse_if()
        elif self.match_token(TokenChoice.current, [TokenTag.KEYWORD]) and temp_lexeme == 'return':
            return self.parse_return()
        elif self.match_token(TokenChoice.current, [TokenTag.TYPENAME_VOID, TokenTag.TYPENAME_CHAR, TokenTag.TYPENAME_INT]):
            return self.parse_variable()
        else:
            return self.parse_expr_stmt()

    def parse_expr_stmt(self) -> ast.Stmt:
        temp_inner_expr = self.parse_expr()
        self.consume_token([TokenTag.SEMICOLON])
        return ast.ExprStmt(temp_inner_expr, ast.OpType.OP_NONE)

    def parse_params(self) -> list[tuple[ast.DataType, str]]:
        self.consume_token([TokenTag.PAREN_OPEN])

        temp_params = []

        if self.match_token(TokenChoice.current, [TokenTag.PAREN_CLOSE]):
            self.consume_token([])
            return temp_params

        while True:
            if self.peek_curr() is None:
                raise SyntaxError('Missing closing parenthesis for parameter list!')

            self.consume_token([TokenTag.TYPENAME_CHAR, TokenTag.TYPENAME_INT])

            temp_param_typename = TYPENAME_TABLE.get(self.peek_prev()[0]) or ast.DataType.TYPENAME_VOID
            temp_param_name = self.peek_curr()[0]

            temp_params.append((temp_param_typename, temp_param_name))

            self.consume_token([TokenTag.IDENTIFIER])

            if self.match_token(TokenChoice.current, [TokenTag.PAREN_CLOSE]):
                self.consume_token([])
                break
            elif self.match_token(TokenChoice.current, [TokenTag.COMMA]):
                self.consume_token([])

        return temp_params

    def parse_args(self) -> list[ast.Expr]:
        self.consume_token([TokenTag.PAREN_OPEN])

        temp_args = []

        if self.match_token(TokenChoice.current, [TokenTag.PAREN_CLOSE]):
            self.consume_token([])
            return temp_args

        while True:
            if self.peek_curr() is None:
                raise SyntaxError('Missing closing parenthesis for argument list!')

            temp_args.append(self.parse_expr())

            if self.match_token(TokenChoice.current, [TokenTag.PAREN_CLOSE]):
                self.consume_token([])
                break
            elif self.match_token(TokenChoice.current, [TokenTag.COMMA]):
                self.consume_token([])

        return temp_args

    def parse_if(self) -> ast.Stmt:
        self.consume_token([])
        self.consume_token([TokenTag.PAREN_OPEN])

        temp_cond = self.parse_expr()

        self.consume_token([TokenTag.PAREN_CLOSE])

        temp_main_block = self.parse_block()

        if self.match_token(TokenChoice.current, [TokenTag.KEYWORD]) and self.peek_curr()[0] == 'else':
            return ast.If(temp_cond, temp_main_block, self.parse_else())

        return ast.If(temp_cond, temp_main_block, None)

    def parse_else(self) -> ast.Stmt:
        self.consume_token([]) # NOTE skip 'else' since I only care about its block!

        return self.parse_block()

    def parse_return(self) -> ast.Stmt:
        self.consume_token([]) # NOTE skip 'return' since the expr matters most!

        temp_result_expr = self.parse_expr()
        self.consume_token([TokenTag.SEMICOLON])

        return ast.Return(temp_result_expr)

    def parse_all(self) -> ParseResult:
        stmts: list[ast.Stmt] = []

        self.consume_token([])

        try:
            while not self.at_end():
                stmts.append(self.parse_declaration())
        except SyntaxError as e:
            self.error_count += 1
            print(f'Parse Error at {self.curr[1]} with \"{self.curr[0]}\":\n{e}')

        return (self.error_count == 0, stmts)
