"""
    ir_types.py\n
    By DrkWithT\n
    Defines 3-address code IR types.
"""

import dataclasses
from enum import Enum, auto
from DerkCC.DCCStages.ast_nodes import DataType

## Aliases and Types ##

class IRType(Enum):
    LABEL = auto()         # <name>:
    RETURN = auto()        # Return
    JUMP = auto()          # Jump <name>
    JUMP_IF = auto()       # JumpIf
    ARGV_PUSH = auto()     # PushArg <arg>
    FUNC_CALL = auto()     # Call <name>
    STORE_YIELD = auto()   # StoreYield <result??>
    LOAD_PARAM = auto()   # StoreParam <addr>
    ADDR_ASSIGN = auto()   # <addr> = <addr> <op> <addr>
    LOAD_CONSTANT = auto() # $<integral>

class IROp(Enum):
    CALL = auto()
    NEGATE = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    ADD = auto()
    SUBTRACT = auto()
    COMPARE_EQ = auto()
    COMPARE_NEQ = auto()
    COMPARE_LT = auto()
    COMPARE_LTE = auto()
    COMPARE_GT = auto()
    COMPARE_GTE = auto()
    SET_VALUE = auto()
    NOP = auto()

AST_OP_IR_MATCHES = {
    "OP_CALL": IROp.CALL,
    "OP_NEG": IROp.NEGATE,
    "OP_MULT": IROp.MULTIPLY,
    "OP_DIV": IROp.DIVIDE,
    "OP_ADD": IROp.ADD,
    "OP_SUB": IROp.SUBTRACT,
    "OP_EQUALITY": IROp.COMPARE_EQ,
    "OP_INEQUALITY": IROp.COMPARE_NEQ,
    "OP_LT": IROp.COMPARE_LT,
    "OP_LTE": IROp.COMPARE_LTE,
    "OP_GT": IROp.COMPARE_GT,
    "OP_GTE": IROp.COMPARE_GTE,
    "OP_LOGIC_AND": IROp.NOP,
    "OP_LOGIC_OR": IROp.NOP,
    "OP_ASSIGN": IROp.NOP,
    "OP_NONE": IROp.NOP
}

AST_OP_IR_INVERSES = {
    "OP_EQUALITY": IROp.COMPARE_NEQ,
    "OP_INEQUALITY": IROp.COMPARE_EQ,
    "OP_LT": IROp.COMPARE_GTE,
    "OP_LTE": IROp.COMPARE_GT,
    "OP_GT": IROp.COMPARE_LTE,
    "OP_GTE": IROp.COMPARE_LT
}

DATATYPE_SIZES = {
    "CHAR": 1,
    "INT": 4,
    "VOID": 0,
    "UNKNOWN": 0
}

class IRStep:
    def get_ir_type(self) -> IRType:
        pass

    def accept_visitor(self, visitor) -> "any":
        pass

StepList = list[IRStep]

## IR models ##

@dataclasses.dataclass
class IRLabel(IRStep):
    title: str

    def get_ir_type(self) -> IRType:
        return IRType.LABEL

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_label(self)

@dataclasses.dataclass
class IRReturn(IRStep):
    result_addr: str

    def get_ir_type(self) -> IRType:
        return IRType.RETURN

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_return(self)

@dataclasses.dataclass
class IRJump(IRStep):
    target: str

    def get_ir_type(self) -> IRType:
        return IRType.JUMP

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_jump(self)

@dataclasses.dataclass
class IRJumpIf(IRStep):
    target: str
    op: IROp
    arg0: str | int
    arg1: str | int

    def get_ir_type(self) -> IRType:
        return IRType.JUMP_IF

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_jump_if(self)

@dataclasses.dataclass
class IRPushArg(IRStep):
    arg: str | int
    immediate: bool
    arg_type: DataType

    def get_ir_type(self) -> IRType:
        return IRType.ARGV_PUSH

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_push_arg(self)

@dataclasses.dataclass
class IRCallFunc(IRStep):
    callee: str

    def get_ir_type(self) -> IRType:
        return IRType.FUNC_CALL

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_call_func(self)

@dataclasses.dataclass
class IRStoreYield(IRStep):
    target: str

    def get_ir_type(self) -> IRType:
        return IRType.STORE_YIELD

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_store_yield(self)

@dataclasses.dataclass
class IRLoadParam(IRStep):
    target: str

    def get_ir_type(self) -> IRType:
        return IRType.LOAD_PARAM

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_load_param(self)

@dataclasses.dataclass
class IRAssign(IRStep):
    dest: str
    op: IROp
    arg0: str | int
    arg1: str | int | None

    def get_ir_type(self) -> IRType:
        return IRType.ADDR_ASSIGN

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_assign(self)

@dataclasses.dataclass
class IRLoadConst(IRStep):
    addr: str
    value: int

    def get_ir_type(self) -> IRType:
        return IRType.LOAD_CONSTANT

    def accept_visitor(self, visitor) -> "any":
        return visitor.visit_load_const(self)
