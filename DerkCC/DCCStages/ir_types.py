"""
     py\n
    By DrkWithT\n
    Defines 3-address code IR types.
"""

import dataclasses
from enum import Enum, auto

## Aliases and Types ##

class IRType(Enum):
    LABEL = auto()         # <name>:
    RETURN = auto()        # Return
    JUMP = auto()          # Jump <name>
    JUMP_IF = auto()       # JumpIf
    ARGV_PUSH = auto()     # PushArg <arg>
    FUNC_CALL = auto()     # Call <name>
    ADDR_DECLARE = auto()  # <addr> = <expr>
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

StepList = list[IRStep]

## IR models ##

@dataclasses.dataclass
class IRLabel(IRStep):
    title: str

    def get_ir_type(self) -> IRType:
        return IRType.LABEL

@dataclasses.dataclass
class IRReturn(IRStep):
    result_addr: str

    def get_ir_type(self) -> IRType:
        return IRType.RETURN

@dataclasses.dataclass
class IRJump( IRStep):
    target: str

    def get_ir_type(self) -> IRType:
        return IRType.JUMP

@dataclasses.dataclass
class IRJumpIf(IRStep):
    target: str
    op: IROp
    arg0: str | int
    arg1: str | int

    def get_ir_type(self) -> IRType:
        return IRType.JUMP_IF

@dataclasses.dataclass
class IRPushArg(IRStep):
    arg: str | int

    def get_ir_type(self) -> IRType:
        return IRType.ARGV_PUSH

@dataclasses.dataclass
class IRCallFunc(IRStep):
    callee: str

    def get_ir_type(self) -> IRType:
        return IRType.FUNC_CALL

@dataclasses.dataclass
class IRAssign(IRStep):
    dest: str
    op: IROp
    operands: list[str | int]

    def get_ir_type(self) -> IRType:
        return IRType.ADDR_ASSIGN

@dataclasses.dataclass
class IRLoadConst(IRStep):
    addr: str
    value: int

    def get_ir_type(self) -> IRType:
        return IRType.LOAD_CONSTANT
