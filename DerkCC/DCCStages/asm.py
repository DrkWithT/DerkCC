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

# FIXME add utilities to allocate registers from various groups: scratch, call, etc. See 9cc compiler repo.

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

ASMLines = list[str]
