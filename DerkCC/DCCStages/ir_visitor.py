"""
    ir_visitor.py\n
    By: DrkWithT\n
    Contains IR visitor interface for the ASM emitter later.
"""

import DerkCC.DCCStages.ir_types as ir_bits

class IRVisitor:
    def visit_label(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_return(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_jump(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_jump_if(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_push_arg(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_store_yield(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_load_param(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_call_func(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_assign(self, step: ir_bits.IRStep) -> "any":
        pass

    def visit_load_const(self, step: ir_bits.IRStep) -> "any":
        pass
