"""
    ASMNode.py\n
    Modified by DrkWithT (Derek Tan)\n
    Contains types modeling GNU assembler for a *nix x64 computer.\n
    See: https://wiki.osdev.org/System_V_ABI
    NOTE the stack must be 16-byte aligned before a call.
    TODO later check a location during ASM generation for role, preserve flag, or the "is argument" flag
"""

import dataclasses
from enum import Enum, auto

## GAS types, aliases, and constants ##

class RegRole(Enum):
    """
        Brief:
        * `RET`: must not be used except for holding return values of callees.
        * `SCRATCH`: free to use for any function.
        * `EXTRA`: must be preserved by callees before use!
    """
    RET = auto()     # rax: DCC will reserve this for return values!
    SCRATCH = auto() # rdi, rsi, rdx, rcx, r8, r9, r10, r11
    EXTRA = auto()   # rbx, rsp, rbp, r12, r13, r14, r15

@dataclasses.dataclass
class RegisterInfo:
    role: RegRole
    preserved: bool
    argy: bool

GAS_REGISTER_HINTS = {
    "%rax": RegisterInfo(RegRole.RET, False, False),
    "%rdi": RegisterInfo(RegRole.SCRATCH, False, True),
    "%rsi": RegisterInfo(RegRole.SCRATCH, False, True),
    "%rdx": RegisterInfo(RegRole.SCRATCH, False, True),
    "%rcx": RegisterInfo(RegRole.SCRATCH, False, True),
    "%r8": RegisterInfo(RegRole.SCRATCH, False, True),
    "%r9": RegisterInfo(RegRole.SCRATCH, False, True),
    "%r10": RegisterInfo(RegRole.SCRATCH, False, False),
    "%r11": RegisterInfo(RegRole.SCRATCH, False, False),
    "%rbx": RegisterInfo(RegRole.EXTRA, True, False),
    "%rsp": RegisterInfo(RegRole.EXTRA, True, False),
    "%rbp": RegisterInfo(RegRole.EXTRA, True, False),
    "%r12": RegisterInfo(RegRole.EXTRA, True, False),
    "%r13": RegisterInfo(RegRole.EXTRA, True, False),
    "%r14": RegisterInfo(RegRole.EXTRA, True, False),
    "%r15": RegisterInfo(RegRole.EXTRA, True, False)
}

@dataclasses.dataclass
class LocationInfo:
    gas_name: str
    used: bool

C_TYPE_SIZES = {
    "CHAR": 1,
    "INT": 4,
    "VOID": 0,
    "UNKNOWN": 0
}

MemTable = dict[str, LocationInfo]
ASMLines = list[str]
