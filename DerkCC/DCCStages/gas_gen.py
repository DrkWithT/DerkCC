"""
    asmgen.py\n
    Modified by DrkWithT\n
    Generates GNU assembler for x64, System V calling convention.\n
    Sources:
    [GAS LMU Lecture](https://cs.lmu.edu/~ray/notes/gasexamples/)\n
    [9cc gen_x86 code](https://github.com/rui314/9cc/blob/master/gen_x86.c)\n
    TODO Overhaul the register/location allocation logic... see 9cc code.
"""

import dataclasses
from enum import Enum, auto
from DerkCC.DCCStages.ast_nodes import DataType
import DerkCC.DCCStages.ir_types as ir_bits
import DerkCC.DCCStages.ir_gen as ir_gen
from DerkCC.DCCStages.ir_visitor import IRVisitor

## Utility types ##

@dataclasses.dataclass
class LocationInfo:
    gas_name: str
    used: bool

class RegisterKind(Enum):
    GENERAL = auto()
    ARG = auto()

## Constants ##

C_TYPE_SIZES = {
    "CHAR": 1,
    "INT": 4,
    "VOID": 0,
    "UNKNOWN": 0
}

IR_COMPARE_TO_JMP = {
    "COMPARE_NEQ": "jne",
    "COMPARE_EQ": "je",
    "COMPARE_LT": "jl",
    "COMPARE_LTE": "jle",
    "COMPARE_GT": "jg",
    "COMPARE_GTE": "jge"
}

IR_OP_TO_GAS = {
    "NEGATE": "neg",
    "MULTIPLY": "mul",
    "DIVIDE": "div",
    "ADD": "add",
    "SUBTRACT": "sub",
    "COMPARE_NEQ": "cmovne",
    "COMPARE_EQ": "cmove",
    "COMPARE_LT": "cmovl",
    "COMPARE_LTE": "cmovle",
    "COMPARE_GT": "cmovg",
    "COMPARE_GTE": "cmovge",
    "NOP": "nop"
}

GENERAL_REGS_64 = ['%r10', '%r11', '%rbx', '%r12', '%r13', '%r14', '%r15']
# GENERAL_REGS_32 = ['r10d', 'r11d', 'ebx', 'r12d', 'r13d', 'r14d', 'r15d']
ARG_REGS_64 = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']
# ARG_REGS_32 = ['edi', 'esi', 'edx', 'ecx', 'r8d', 'r9d']
RET_REG = '%rax'

## Aliases ##

RegTable = dict[str, bool]
IRSteps = list[ir_bits.IRStep]
ASMLines = list[str]

## Utility functions ##

def roundup_offset(acc_offset: int, align_n: int = 16):
    # NOTE from 9cc repo: https://github.com/rui314/9cc/blob/master/gen_x86.c
    mask = align_n - 1
    return (acc_offset + mask) & ~(mask)

## Register Allocator ##

class RegisterAllocator:
    gen_pool: RegTable
    arg_names: list[str]
    arg_pool: RegTable
    gen_lru: list[str]
    arg_lru: list[str]

    def __init__(self):
        self.gen_names = [gen for gen in GENERAL_REGS_64]
        self.gen_pool = {}
        self.arg_names = [arg for arg in ARG_REGS_64]
        self.arg_pool = {}
        self.gen_lru = []
        self.arg_lru = []

        for reg64 in GENERAL_REGS_64:
            self.gen_pool[reg64] = False

        for arg64 in ARG_REGS_64:
            self.arg_pool[arg64] = False

    def release_all(self, kind: RegisterKind):
        if kind == RegisterKind.GENERAL:
            self.gen_lru.clear()

            for gen in self.gen_pool:
                self.gen_pool[gen] = False
        elif kind == RegisterKind.ARG:
            self.arg_lru.clear()

            for arg in self.arg_pool:
                self.arg_pool[arg] = False

    def salvage_oldest_reg(self, kind: RegisterKind) -> str | None:
        pool_ref = self.gen_pool if kind == RegisterKind.GENERAL else self.arg_pool
        lru_ref = self.gen_lru if kind == RegisterKind.GENERAL else self.arg_lru

        if not lru_ref or (kind == RegisterKind.ARG and len(lru_ref) >= 6):
            return None

        target = lru_ref.pop(0)
        pool_ref[target] = True

        return target

    def get_ret_reg(self) -> str:
        return '%rax'

    def allocate_reg(self, kind: RegisterKind) -> str | None:
        if kind == RegisterKind.ARG:
            for reg in self.arg_names:
                if not self.arg_pool.get(reg):
                    self.arg_pool[reg] = True
                    self.arg_lru.append(reg)
                    return reg
        else:
            for reg in self.gen_pool:
                if not self.gen_pool.get(reg):
                    self.gen_pool[reg] = True
                    self.gen_lru.append(reg)
                    return reg

        return self.salvage_oldest_reg(kind)

    def release_reg(self, reg: str) -> bool:
        if reg in self.gen_pool:
            self.gen_pool[reg] = False
        elif reg in self.arg_pool:
            self.arg_pool[reg] = False

## Temp Allocator ##

class TempAllocator:
    temp_pool: dict[str, bool]
    frame_offset: int
    max_local_count: int
    local_count: int

    def __init__(self):
        self.temp_pool = {}
        self.frame_offset = 0
        self.max_local_count = 0
        self.local_count = 0

    def get_frame_offset(self) -> int:
        return self.frame_offset

    def reset_state(self, local_n: int):
        self.temp_pool.clear()
        self.frame_offset = 0
        self.max_local_count = local_n
        self.local_count = 0

    def allocate_temp(self, var: ir_gen.LocalRecord) -> str | None:
        if self.local_count >= self.max_local_count:
            return None

        var_datatype = var[0].name
        var_size = C_TYPE_SIZES.get(var_datatype)

        if var_size == 0:
            return None

        self.frame_offset += var_size
        # NOTE alignment requirement means each object with a valid type must have their beginnings allocated N bytes apart (their data-type size)... Powers of 2
        self.frame_offset = roundup_offset(self.frame_offset, var_size)

        result_addr = f'-{self.frame_offset}(%rbp)'
        self.temp_pool[result_addr] = True
        self.local_count += 1

        return result_addr

    def release_temp(self, gas_temp_addr: str) -> bool:
        if gas_temp_addr not in self.temp_pool.keys():
            return False

        self.temp_pool[gas_temp_addr] = False
        self.local_count -= 1
        return True

## Emitter ##

class GASEmitter(IRVisitor):
    func_info: ir_gen.FuncInfoTable
    reg_allocator: RegisterAllocator
    temp_allocator: TempAllocator
    ir_to_gasreg: dict[str, str]
    ir_to_gastemp: dict[str, str]
    current_funcinfo: ir_gen.FuncInfo
    results: ASMLines

    def __init__(self, funcs: ir_gen.FuncInfoTable):
        super().__init__()
        self.func_info = funcs
        self.reg_allocator = RegisterAllocator()
        self.temp_allocator = TempAllocator()
        self.ir_to_gasreg = {}
        self.ir_to_gastemp = {}
        self.current_funcinfo = None
        self.results = []

    def emit_all(self, steps: IRSteps) -> ASMLines:
        self.results.append('; generated by DCC v0.1 alpha\n')
        self.results.append('.text\n')
        for step in steps:
            step.accept_visitor(self)

        return self.results

    def visit_label(self, step: ir_bits.IRStep):
        label_name: str = step.title

        if label_name[0] == 'L':
            self.results.append(f'{step.title}:\n')
        else:
            self.results.append(f'.global {label_name}\n')
            self.results.append(f'{label_name}:\n')

            # 1. allocate the stack frame
            self.results.append(f'\tpushq %rbp\n')
            self.results.append(f'\tmovq %rsp, %rbp\n')

            # 2. allocate params and locals to stack locations...
            self.current_funcinfo = [item for item in self.func_info.get(label_name)]
            self.temp_allocator.reset_state(len(self.current_funcinfo))

            for fn_local in self.current_funcinfo:
                datatype, ir_addr, is_param = fn_local

                if datatype == DataType.UNKNOWN:
                    break

                if is_param is not False:
                    param_dest = self.temp_allocator.allocate_temp(fn_local)
                    self.ir_to_gastemp[ir_addr] = param_dest
                else:
                    var_dest = self.temp_allocator.allocate_temp(fn_local)
                    self.ir_to_gastemp[ir_addr] = var_dest

            self.results.append(f'\tsubq ${self.temp_allocator.get_frame_offset()}, %rbp\n')

            # 3. this function will preserve some special registers
            self.results.append(f'\tpushq %r12\n')
            self.results.append(f'\tpushq %r13\n')
            self.results.append(f'\tpushq %r14\n')
            self.results.append(f'\tpushq %r15\n')

    def visit_return(self, step: ir_bits.IRStep):
        result_gas_addr = self.ir_to_gasreg.get(step.result_addr) or self.ir_to_gastemp.get(step.result_addr)

        self.results.append(f'\tmovq {result_gas_addr}, {self.reg_allocator.get_ret_reg()}')
        self.results.append(f'\tpopq %r15\n')
        self.results.append(f'\tpopq %r14\n')
        self.results.append(f'\tpopq %r13\n')
        self.results.append(f'\tpopq %r12\n')
        self.results.append(f'\tmov %rbp, %rsp\n')
        self.results.append(f'\tpopq %rbp\n')
        self.results.append(f'\tret\n')

        self.ir_to_gastemp.clear()
        self.temp_allocator.reset_state(0)
        self.ir_to_gasreg.clear()
        self.reg_allocator.release_all(RegisterKind.GENERAL)
        self.reg_allocator.release_all(RegisterKind.ARG)
        self.current_funcinfo = None

    def visit_jump(self, step: ir_bits.IRStep):
        target_label: str = step.target
        self.results.append(f'\tjmp {target_label}\n')

    def visit_jump_if(self, step: ir_bits.IRStep):
        jump_dest = step.target
        jump_ir_op: ir_bits.IROp = step.op
        jump_ir_arg0: str | int = step.arg0
        jump_ir_arg1: str | int = step.arg1

        gas_cond_arg0 = self.ir_to_gasreg.get(jump_ir_arg0) or self.ir_to_gastemp.get(jump_ir_arg0) if type(jump_ir_arg0) != int else f'${jump_ir_arg0}'
        gas_cond_arg1 = self.ir_to_gasreg.get(jump_ir_arg1) or self.ir_to_gastemp.get(jump_ir_arg1) if type(jump_ir_arg1) != int else f'${jump_ir_arg1}'

        gas_cond_jump = IR_COMPARE_TO_JMP.get(jump_ir_op.name)

        if gas_cond_jump != 'nop':
            self.results.append(f'\tcmp {gas_cond_arg1}, {gas_cond_arg0}\n')

        match gas_cond_jump:
            case 'jne':
                self.results.append(f'\tjne {jump_dest}\n')
            case 'je':
                self.results.append(f'\tje {jump_dest}\n')
            case 'jl':
                self.results.append(f'\tjl {jump_dest}\n')
            case 'jle':
                self.results.append(f'\tjle {jump_dest}\n')
            case 'jg':
                self.results.append(f'\tjg {jump_dest}\n')
            case 'jge':
                self.results.append(f'\tjge {jump_dest}\n')
            case 'nop':
                pass

        if type(gas_cond_arg0) == int:
            pass
        elif gas_cond_arg0 is not None and gas_cond_arg0[0] == '-':
            self.temp_allocator.release_temp(gas_cond_arg0)
        elif gas_cond_arg0 is not None:
            self.reg_allocator.release_reg(gas_cond_arg0)

        if type(gas_cond_arg1) == int:
            pass
        elif gas_cond_arg1 is not None and gas_cond_arg1[0] == '-':
            self.temp_allocator.release_temp(gas_cond_arg1)
        elif gas_cond_arg0 is not None:
            self.reg_allocator.release_reg(gas_cond_arg1)

    def visit_push_arg(self, step: ir_bits.IRStep):
        ir_arg: str | int = step.arg

        arg_dest = self.reg_allocator.allocate_reg(RegisterKind.ARG)

        if not arg_dest:
            raise RuntimeError(f'gas_gen.py [Error]: Could not allocate arg register, stack args unsupported!\n')

        if type(ir_arg) == int:
            self.results.append(f'\tmovq ${ir_arg}, {arg_dest}\n')
        else:
            arg_src = self.ir_to_gasreg.get(ir_arg) or self.ir_to_gastemp.get(ir_arg)
            self.results.append(f'\tmovq {arg_src}, {arg_dest}\n')

            if arg_src[0] == '-':
                self.temp_allocator.release_temp(arg_src)
            else:
                self.reg_allocator.release_reg(arg_src)

    def visit_store_yield(self, step: ir_bits.IRStep):
        result_ir_dest: str = step.target
        result_gas_dest = self.ir_to_gasreg.get(result_ir_dest) or self.ir_to_gastemp.get(result_ir_dest)

        if not result_gas_dest:
            result_gas_dest = self.reg_allocator.allocate_reg(RegisterKind.GENERAL)
            self.ir_to_gasreg[result_ir_dest] = result_gas_dest

        self.results.append(f'\tmovq %rax, {result_gas_dest}\n')

    def visit_load_param(self, step: ir_bits.IRStep):
        param_gas_src: str = self.reg_allocator.allocate_reg(RegisterKind.ARG)
        param_info = self.current_funcinfo.pop(0)
        param_ir_src: str = param_info[1]
        param_gas_dst: str = self.ir_to_gastemp.get(param_ir_src)

        if not param_gas_dst:
            param_gas_dst = self.temp_allocator.allocate_temp(param_info)

        self.results.append(f'\tmovq {param_gas_src}, {param_gas_dst}\n')

    def visit_call_func(self, step: ir_bits.IRStep):
        self.results.append(f'\tpush %r10\n')
        self.results.append(f'\tpush %r11\n')
        self.results.append(f'\txor %rax, %rax\n')
        self.results.append(f'\tcall {step.callee}\n')
        self.results.append(f'\tpop %r11\n')
        self.results.append(f'\tpop %r10\n')

    def visit_assign(self, step: ir_bits.IRStep):
        ir_dest: str = step.dest
        ir_op: ir_bits.IROp = step.op
        ir_arg0: str | int = step.arg0
        ir_arg1: str | int | None = step.arg1 or '?'
        
        gas_op = IR_OP_TO_GAS.get(ir_op.name) or '?'

        dest_gas_addr = dest_gas_addr = self.ir_to_gastemp.get(ir_dest)

        if not dest_gas_addr:
            dest_gas_addr = self.reg_allocator.allocate_reg(RegisterKind.GENERAL)
            self.ir_to_gasreg[ir_dest] = dest_gas_addr
        else:
            self.ir_to_gastemp[ir_dest] = dest_gas_addr

        arg0_gas_addr = self.ir_to_gasreg.get(ir_arg0) or self.ir_to_gastemp.get(ir_arg0)
        arg1_gas_addr = self.ir_to_gasreg.get(ir_arg1) or self.ir_to_gastemp.get(ir_arg1)

        if not arg0_gas_addr:
            arg0_gas_addr = f'${ir_arg0}'
        if not arg1_gas_addr:
            arg1_gas_addr = f'${ir_arg1}'

        match gas_op:
            case 'neg':
                self.results.append(f'\tneg {arg0_gas_addr}\n')
                self.results.append(f'\tmovq {arg0_gas_addr}, {dest_gas_addr}\n')
            case 'add':
                self.results.append(f'\tmovq {arg0_gas_addr}, {dest_gas_addr}\n')
                self.results.append(f'\tadd {arg1_gas_addr}, {dest_gas_addr}\n')
            case 'sub':
                self.results.append(f'\tmovq {arg1_gas_addr}, {dest_gas_addr}\n')
                self.results.append(f'\tsubq {arg0_gas_addr}, {dest_gas_addr}\n')
            case 'mul':
                self.results.append(f'\tnop\n') # FIXME
                pass
            case 'div':
                self.results.append(f'\tnop\n') # FIXME
                pass
            case 'cmovne':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmovne $1, {dest_gas_addr}\n')
            case 'cmove':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmove $1, {dest_gas_addr}\n')
            case 'cmovl':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmovl $1, {dest_gas_addr}\n')
            case 'cmovle':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmovle $1, {dest_gas_addr}\n')
            case 'cmovg':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmovg $1, {dest_gas_addr}\n')
            case 'cmovge':
                self.results.append(f'\tmovq $0, {dest_gas_addr}\n')
                self.results.append(f'\tcmp {arg1_gas_addr}, {arg0_gas_addr}\n')
                self.results.append(f'\tcmovge $1, {dest_gas_addr}\n')
            case 'nop':
                self.results.append(f'\tmovq {arg0_gas_addr}, {dest_gas_addr}\n')

        if type(arg0_gas_addr) == str and arg0_gas_addr[0] != '-':
            self.reg_allocator.release_reg(arg0_gas_addr)
        elif type(arg0_gas_addr) == str and arg0_gas_addr[0] == '%':
            self.temp_allocator.release_temp(arg0_gas_addr)

        if type(arg1_gas_addr) == str and arg1_gas_addr[0] != '-':
            self.reg_allocator.release_reg(arg1_gas_addr)
        elif type(arg1_gas_addr) == str and arg0_gas_addr[0] == '%':
            self.temp_allocator.release_temp(arg1_gas_addr)

    def visit_load_const(self, step: ir_bits.IRStep):
        ir_const_addr: str = step.addr
        ir_constant: int = step.value
        func_const_info = None
        print(self.current_funcinfo)

        for entry in self.current_funcinfo:
            if entry[1] == ir_const_addr:
                func_const_info = entry
                break

        ir_const_gas_addr = self.temp_allocator.allocate_temp(func_const_info) or self.reg_allocator.allocate_reg(RegisterKind.GENERAL)

        if ir_const_gas_addr[0] == '-':
            self.ir_to_gastemp[ir_const_addr] = ir_const_gas_addr
        else:
            self.ir_to_gasreg[ir_const_addr] = ir_const_gas_addr

        self.results.append(f'\tmovq ${ir_constant}, {ir_const_gas_addr}\n')
