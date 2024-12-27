"""
    ast_nodes.py\n
    Modified by DrkWithT (Derek Tan)\n
    NOTE Should add ExprType enum to discern arg vs. param types later.
"""

from enum import Enum, auto
from pyCC.pyCmp.lexer import TokenObj
import pyCC.pyCmp.ast_visitor as pycc_ast_visitor

## Enums, Types ##

TreeVisitor = pycc_ast_visitor.ASTVisitor

class DataType(Enum):
    CHAR = 0
    INT = 1
    VOID = 2
    UNKNOWN = 3

class OpArity(Enum):
    UNARY = auto()
    BINARY = auto()
    NOTHING = auto()

class OpType(Enum):
    OP_CALL = auto()
    OP_NEG = auto()
    OP_MULT = auto()
    OP_DIV = auto()
    OP_ADD = auto()
    OP_SUB = auto()
    OP_EQUALITY = auto()
    OP_INEQUALITY = auto()
    OP_LT = auto()
    OP_LTE = auto()
    OP_GT = auto()
    OP_GTE = auto()
    OP_LOGIC_AND = auto()
    OP_LOGIC_OR = auto()
    OP_ASSIGN = auto()
    OP_NONE = auto()

ParamList = list[tuple[DataType, str]]

## Constants ##

OP_ARITY_TABLE = {
    "OP_CALL": OpArity.UNARY,
    "OP_NEG": OpArity.UNARY,
    "OP_MULT": OpArity.BINARY,
    "OP_DIV": OpArity.BINARY,
    "OP_ADD": OpArity.BINARY,
    "OP_SUB": OpArity.BINARY,
    "OP_EQUALITY": OpArity.BINARY,
    "OP_INEQUALITY": OpArity.BINARY,
    "OP_LT": OpArity.BINARY,
    "OP_LTE": OpArity.BINARY,
    "OP_GT": OpArity.BINARY,
    "OP_GTE": OpArity.BINARY,
    "OP_ASSIGN": OpArity.BINARY,
    "OP_NONE": OpArity.NOTHING
}

## Base Classes ##

class Expr:
    def deduce_early_type(self) -> DataType:
        pass

    def get_op_arity(self) -> OpArity:
        pass

    def get_op_type(self) -> OpType:
        pass

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        pass

class Stmt:
    def is_expr_stmt(self) -> bool:
        pass

    def is_declaration(self) -> bool:
        pass

    def is_control_flow(self) -> bool:
        pass

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        pass

## Expressions ##

class Literal(Expr):
    ArrayType = list[Expr]
    LiteralData = tuple[TokenObj, ArrayType | None];

    def __init__(self, data: LiteralData, data_type: DataType):
        super().__init__()

        data_0, data_1 = data;

        self.data = data

        if data_0 is not None:
            self.arr_flag = False
            self.data_type = data_type
        elif data_1 is not None:
            self.arr_flag = True
            self.data_type = data_type
        else:
            self.arr_flag = False
            self.data_type = DataType.UNKNOWN

    def is_array(self) -> bool:
        return self.arr_flag

    def get_data(self) -> LiteralData:
        return self.data

    def deduce_early_type(self) -> DataType:
        return self.data_type

    def get_op_arity(self) -> OpArity:
        return OpArity.NOTHING

    def get_op_type(self) -> OpType:
        return OpType.OP_NONE

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_literal(self)

class Unary(Expr):
    def __init__(self, inner: Expr, op: OpType):
        super().__init__()
        self.inner = inner
        self.op = op

    def get_inner(self) -> Expr:
        return self.inner

    def deduce_early_type(self) -> DataType:
        return self.inner.deduce_early_type()

    def get_op_arity(self) -> OpArity:
        return OpArity.UNARY

    def get_op_type(self) -> OpType:
        return self.op

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_unary(self)

class Binary(Expr):
    def __init__(self, lhs: Expr, rhs: Expr, op: OpType):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_lhs(self) -> Expr:
        return self.lhs

    def get_rhs(self) -> Expr:
        return self.rhs

    def deduce_early_type(self) -> DataType:
        if self.lhs.deduce_early_type() == self.rhs.deduce_early_type():
            return self.lhs.deduce_early_type()

        return DataType.UNKNOWN

    def get_op_arity(self) -> OpArity:
        return OpArity.BINARY

    def get_op_type(self) -> OpType:
        return self.op

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_binary(self)

class Call(Expr):
    ArgList = list[Expr]

    def __init__(self, name: str, args: ArgList):
        super().__init__()
        self.name = name
        self.args = args

    def get_name(self) -> str:
        return self.name

    def get_args(self) -> ArgList:
        return self.args

    def deduce_early_type(self) -> DataType:
        """
            NOTE Requires external symbol lookup instead to deduce the result type.\n
            EXAMPLE: `int foo(int a, int b);` gives `int`.
        """
        return DataType.UNKNOWN

    def get_op_arity(self) -> OpArity:
        return OpArity.NOTHING

    def get_op_type(self) -> OpType:
        return OpType.OP_CALL

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_call(self)

## Statements ##

class Variable(Stmt):
    # TODO add type qualifier support??
    def __init__(self, name: str, var_type: DataType, rhs: Expr):
        super().__init__()
        self.name = name
        self.var_type = var_type
        self.rhs = rhs

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> DataType:
        return self.var_type

    def get_rhs(self) -> Expr:
        return self.rhs

    def is_expr_stmt(self) -> bool:
        return False

    def is_declaration(self) -> bool:
        return True

    def is_control_flow(self) -> bool:
        return False

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_variable_decl(self)

class Block(Stmt):
    """
        NOTE This only represents a block of executable statements.
    """
    def __init__(self, stmts: list[Stmt]):
        super().__init__()
        self.stmts = stmts
    
    def get_stmts(self) -> list[Stmt]:
        return self.stmts
    
    def is_expr_stmt(self) -> bool:
        return False

    def is_declaration(self) -> bool:
        return False

    def is_control_flow(self) -> bool:
        return True

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_block(self)

class FunctionDecl(Stmt):
    def __init__(self, name: str, result_type: DataType, params: ParamList, body: list[Stmt]):
        super().__init__()
        self.name = name
        self.result_type = result_type
        self.params = params
        self.body = body

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> DataType:
        return self.result_type

    def get_params(self) -> ParamList:
        return self.params

    def get_arity(self) -> int:
        return len(self.params)

    def get_body(self) -> Stmt:
        return self.body

    def is_expr_stmt(self) -> bool:
        return False

    def is_declaration(self) -> bool:
        return True

    def is_control_flow(self) -> bool:
        return False

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_function_decl(self)

class ExprStmt(Stmt):
    def __init__(self, inner: Expr, op: OpType):
        super().__init__()
        self.inner = inner
        self.outer_op = op

    def get_inner(self) -> Expr:
        return self.inner

    def get_outer_op(self) -> OpType:
        return self.outer_op

    def is_expr_stmt(self) -> bool:
        """
            NOTE The name is wrong, as this function should check if this expr-stmt is worth generating as IR. Temporaries are ignored.
        """
        inside_op = self.get_inner().get_op_type()
        return inside_op == OpType.OP_CALL or inside_op == OpType.OP_ASSIGN

    def is_declaration(self) -> bool:
        return False

    def is_control_flow(self) -> bool:
        return False

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_expr_stmt(self)

class If(Stmt):
    def __init__(self, conditional: Expr, body: Stmt, other_body: Stmt | None):
        super().__init__()
        self.conditional = conditional
        self.body = body
        self.other_body = other_body

    def get_conditions(self) -> Expr:
        return self.conditional

    def get_if_body(self) -> Stmt:
        return self.body

    def get_alt_body(self) -> Stmt | None:
        return self.other_body

    def is_expr_stmt(self) -> bool:
        return False

    def is_declaration(self) -> bool:
        return False

    def is_control_flow(self) -> bool:
        return True

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_if(self)

class Return(Stmt):
    def __init__(self, result: Expr):
        super().__init__()
        self.result = result

    def get_result_expr(self) -> Expr:
        return self.result

    def is_expr_stmt(self) -> bool:
        return False

    def is_declaration(self) -> bool:
        return False

    def is_control_flow(self) -> bool:
        return True

    def accept_visitor(self, visitor: TreeVisitor) -> "any":
        return visitor.visit_return(self)
