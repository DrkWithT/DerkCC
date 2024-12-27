"""
    ir_gen.py\n
    Added by DrkWithT\n
    Defines AST to IR converter.\n
    TODO add support for returning values... see visit_return()
"""

import dataclasses
from pyCC.pyCmp.ast_visitor import ASTVisitor
from pyCC.pyCmp.lexer import TokenType
import pyCC.pyCmp.ast_nodes as ast
import pyCC.pyCmp.semantics as sem
import pyCC.pyCmp.ir_types as ir_types

## IR Types ##

@dataclasses.dataclass
class IRLabel(ir_types.IRStep):
    title: str

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.LABEL

@dataclasses.dataclass
class IRReturn(ir_types.IRStep):
    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.RETURN

@dataclasses.dataclass
class IRJump(ir_types.IRStep):
    target: str

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.JUMP

@dataclasses.dataclass
class IRJumpIf(ir_types.IRStep):
    target: str
    op: ir_types.IROp
    arg0: str | int
    arg1: str | int

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.JUMP_IF

@dataclasses.dataclass
class IRPushArg(ir_types.IRStep):
    arg: str | int

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.ARGV_PUSH

@dataclasses.dataclass
class IRCallFunc(ir_types.IRStep):
    callee: str

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.FUNC_CALL

@dataclasses.dataclass
class IRAssign(ir_types.IRStep):
    dest: str
    op: ir_types.IROp
    operands: list[str | int]

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.ADDR_ASSIGN

@dataclasses.dataclass
class IRLoadConst(ir_types.IRStep):
    addr: str
    value: int

    def get_ir_type(self) -> ir_types.IRType:
        return ir_types.IRType.LOAD_CONSTANT

## IR Generator ##

class IREmitter(ASTVisitor):
    AddrUsageTable = dict[str, bool] # NOTE format is "a{num}": bool.

    addr_table: AddrUsageTable = None
    name_to_addr_table: dict = None
    jump_label_i: int = None
    temp_labels: list[str] = []
    frame_sizes: list[int] = None
    results: ir_types.StepList = None

    def __init__(self, sem_info: sem.SemanticsTable):
        self.sem_table = sem_info
        self.addr_table = {
            "A": False, # NOTE True => used!
            "B": False,
            "C": False
        }
        self.name_to_addr_table = {
            "A": None,
            "B": None,
            "C": None
        }
        self.jump_label_i = 0
        self.temp_labels = []
        self.frame_sizes = []
        self.results = []

    def toggle_addr_usage(self, id: str):
        # NOTE an IR address is "used" during initialization or operations.
        if self.addr_table.get(id) is not None:
            # NOTE handles A,B,C addresses...
            temp = not self.addr_table.get(id)
            self.addr_table[id] = temp
        else:
            # NOTE handles new temp addresses of a<n> form... "initialize" it here!
            self.addr_table[id] = False

    def get_available_addrs(self):
        """
            NOTE Gets available (unused) IR address list excluding temps.\n
        """
        availables = filter(lambda a: not self.addr_table.get(a), self.addr_table.keys())
        return [usable_addr for usable_addr in availables]

    def allocate_addr(self):
        """
            Generates the next usable IR address to store an intermediate value if no candidates exist... but a used address can become unused after use for other operations. This logic basically uses memoization of all unoccupied IR addresses. \n
            * If a reserved register is available, use the next one.
            * If not, use an existing temporary register if available.
            * Finally, use a new temporary register if no existing ones are available.
        """
        # pool of at least 1 guaranteed free address...
        candidates = self.get_available_addrs()

        for addr in candidates:
            if self.addr_table.get(addr) != True:
                self.toggle_addr_usage(addr)
                return addr

        # empty pool case:
        new_temp_id = len(self.addr_table) - 3
        new_addr = f'a{new_temp_id}'
        self.toggle_addr_usage(new_addr)
        self.toggle_addr_usage(new_addr)
        return new_addr

    def generate_next_label(self):
        temp_label_i = self.jump_label_i
        self.jump_label_i += 1

        return f'L{temp_label_i}'

    def gen_ir_from_ast(self, ast: list[ast.Stmt]):
        for stmt in ast:
            stmt.accept_visitor(self)

        return self.results

    def generate_normal_jump(self, target_label: str, op: ast.OpType, lhs: ast.Expr, rhs: ast.Expr):
        # NOTE the 3 NOPs for ASSIGN, AND, OR will be handled by caller code instead...
        op = ir_types.AST_OP_IR_MATCHES.get(op.name)
        temp = self.allocate_addr() # a2
        lhs_temp = lhs.accept_visitor(self)
        rhs_temp = rhs.accept_visitor(self)

        self.results.append(IRAssign(temp, op, [lhs_temp, rhs_temp]))
        self.results.append(IRJumpIf(target_label, ir_types.IROp.COMPARE_NEQ, 0, temp))

        self.toggle_addr_usage(temp)
        self.toggle_addr_usage(rhs_temp)
        self.toggle_addr_usage(lhs_temp)

    def generate_inverse_jump(self, target_label: str, expr: ast.Expr):
        op = expr.get_op_type()
        inverse_op = ir_types.AST_OP_IR_INVERSES.get(op.name) or ir_types.IROp.NOP
        op_arity = expr.get_op_arity()

        if inverse_op != ir_types.IROp.NOP:
            lhs_temp = expr.get_lhs().accept_visitor(self)
            rhs_temp = expr.get_rhs().accept_visitor(self)

            self.results.append(IRJumpIf(target_label, inverse_op, lhs_temp, rhs_temp))
            self.toggle_addr_usage(rhs_temp)
            self.toggle_addr_usage(lhs_temp)
        elif op_arity == ast.OpArity.BINARY:
            temp = self.allocate_addr()
            lhs_temp = expr.get_lhs().accept_visitor(self)
            rhs_temp = expr.get_rhs().accept_visitor(self)

            self.results.append(IRAssign(temp, op, [lhs_temp, rhs_temp]))
            self.results.append(IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, temp))
            self.toggle_addr_usage(temp)
            self.toggle_addr_usage(rhs_temp)
            self.toggle_addr_usage(lhs_temp)
        elif op_arity == ast.OpArity.UNARY:
            inner_temp = expr.get_inner().accept_visitor(self)
            temp = self.allocate_addr()
            self.results.append(IRAssign(temp, op, [inner_temp]))
            self.results.append(IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, inner_temp))
            self.toggle_addr_usage(temp)
            self.toggle_addr_usage(inner_temp)
        elif op_arity == ast.OpArity.NOTHING:
            temp = expr.accept_visitor(self)
            self.results.append(IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, temp))
            self.toggle_addr_usage(temp)

    def visit_literal(self, node: ast.Expr) -> tuple[bool, "any"]:
        # NOTE literal_token: Literal.LiteralData & literal_arrtype: Literal.ArrayType
        literal_token, literal_arrtype = node.get_data()

        if literal_token is not None:
            # TODO use allocation of IR address...
            lexeme: str = literal_token[0]
            # raw_value: int = int(lexeme) if literal_token[2] == TokenType.LITERAL_INT else ord(lexeme[0])
            raw_value = 0
            value_addr = self.allocate_addr()

            if literal_token[2] == TokenType.LITERAL_INT:
                raw_value = int(lexeme)
                self.results.append(
                    IRLoadConst(value_addr, raw_value)
                )
            elif literal_token[2] == TokenType.LITERAL_CHAR:
                raw_value = ord(lexeme[0])
                self.results.append(
                    IRLoadConst(value_addr, raw_value)
                )
            elif literal_token[2] == TokenType.IDENTIFIER:
                temp = self.name_to_addr_table.get(lexeme)
                raw_value = temp or 'aX'
                self.results.append(
                    IRLoadConst(value_addr, raw_value)
                )
            return value_addr
        elif literal_arrtype is not None:
            # TODO implement array handling... allocate N addresses where N = arr.length!
            pass

    def visit_unary(self, node: ast.Expr):
        src_addr = node.get_inner().accept_visitor(self)
        op = node.get_op_type()
        dest_addr = self.allocate_addr()

        if op == ast.OpType.OP_NEG:
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NEGATE, [src_addr]))
            self.toggle_addr_usage(src_addr)
            return dest_addr

        return None

    def visit_binary(self, node: ast.Expr):
        expr_lhs: ast.Expr = node.get_lhs()
        expr_rhs: ast.Expr = node.get_rhs()
        op = node.get_op_type()
        dest_addr = self.allocate_addr()

        if op == ast.OpType.OP_LOGIC_AND:
            falsy_label = self.generate_next_label()
            truthy_label = self.generate_next_label()

            self.generate_inverse_jump(falsy_label, expr_lhs)
            self.generate_inverse_jump(falsy_label, expr_rhs)
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NOP, [1]))
            self.results.append(IRJump(truthy_label))

            self.results.append(IRLabel(falsy_label))
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NOP, [0]))
            self.results.append(IRLabel(truthy_label))
        elif op == ast.OpType.OP_LOGIC_OR:
            falsy_label = self.generate_next_label()
            truthy_label = self.generate_next_label()
            skippy_label = self.generate_next_label()

            self.generate_normal_jump(truthy_label, expr_lhs.get_op_type(), expr_lhs, expr_rhs)
            self.generate_normal_jump(truthy_label, expr_rhs.get_op_type(), expr_lhs, expr_rhs)

            self.results.append(IRLabel(truthy_label))
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NOP, [1]))
            self.results.append(IRJump(skippy_label))

            self.results.append(IRLabel(falsy_label))
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NOP, [0]))
            self.results.append(IRLabel(skippy_label))
        elif op != ast.OpType.OP_ASSIGN:
            arg0_addr = expr_lhs.accept_visitor(self)
            arg1_addr = expr_rhs.accept_visitor(self)
            self.results.append(IRAssign(dest_addr, ir_types.IROp(op.value), [arg0_addr, arg1_addr]))

            self.toggle_addr_usage(arg1_addr)
            self.toggle_addr_usage(arg0_addr)
        else:
            value_addr = expr_rhs.accept_visitor(self)
            self.results.append(IRAssign(dest_addr, ir_types.IROp.NOP, [value_addr]))
            self.toggle_addr_usage(value_addr)

        return dest_addr

    def visit_call(self, node: ast.Expr):
        func_name: str = node.get_name()
        func_retype: ast.DataType = self.sem_table.get('.global').get(func_name).data_type
        func_argv: ast.Call.ArgList = node.get_args()

        for arg in func_argv:
            if arg.get_op_type() == ast.OpType.OP_NONE:
                # NOTE either check lexeme of literal for its value...
                temp_lexeme: str = arg.get_data()[0][0]
                temp_value = int(temp_lexeme) if temp_lexeme[0] != '\'' else ord(temp_lexeme[1])
                self.results.append(IRPushArg(temp_value))
            else:
                # ... or just process a temporary value from an arg. expr.
                temp_arg_addr: str = arg.accept_visitor(self)
                self.results.append(IRPushArg(temp_arg_addr))

        if func_retype == ast.DataType.VOID:
            self.results.append(IRCallFunc(func_name))
        elif func_retype != ast.DataType.UNKNOWN:
            dest_addr = self.allocate_addr()
            self.results.append(IRAssign(dest_addr, ir_types.IROp.CALL, [func_name]))
            return dest_addr

    def visit_variable_decl(self, node: ast.Stmt):
        var_addr = self.allocate_addr()
        self.name_to_addr_table[node.get_name()] = var_addr
        rhs_addr: str = node.get_rhs().accept_visitor(self)
        self.results.append(IRAssign(var_addr, ir_types.IROp.NOP, [rhs_addr]))
        return var_addr

    def visit_block(self, node: ast.Stmt):
        for stmt in node.get_stmts():
            stmt.accept_visitor(self)

    def visit_function_decl(self, node: ast.Stmt):
        func_name: str = node.get_name()
        func_param_v: ast.ParamList = node.get_params()

        self.results.append(IRLabel(func_name))

        for param in func_param_v:
            param_addr = self.allocate_addr()
            self.name_to_addr_table[param[1]] = param_addr
            self.results.append(IRLoadConst(param_addr, 0))

        ret_label = self.generate_next_label()
        self.temp_labels.append(ret_label)

        node.get_body().accept_visitor(self)

        self.results.append(IRLabel(ret_label))
        self.results.append(IRReturn())
        self.temp_labels.clear()
        self.name_to_addr_table.clear()

    def visit_expr_stmt(self, node: ast.Stmt):
        op = node.get_inner().get_op_type()

        if op == ast.OpType.OP_CALL or op == ast.OpType.OP_ASSIGN:
            node.get_inner().accept_visitor(self)

    def visit_if(self, node: ast.Stmt):
        truthy_body: ast.Stmt = node.get_if_body()
        falsy_body: ast.Stmt = node.get_alt_body()
        falsy_label = self.generate_next_label()

        cond_addr = node.get_conditions().accept_visitor(self)
        self.results.append(IRJumpIf(falsy_label, ir_types.IROp.COMPARE_EQ, 0, cond_addr))

        truthy_body.accept_visitor(self)

        if falsy_body is not None:
            truthy_label = self.generate_next_label()

            self.results.append(IRJump(truthy_label))
            self.results.append(IRLabel(falsy_label))
            falsy_body.accept_visitor(self)
            self.results.append(IRLabel(truthy_label))
        else:
            self.results.append(IRLabel(falsy_label))

        self.toggle_addr_usage(cond_addr)

    def visit_return(self, node: ast.Stmt):
        self.results.append(IRJump(self.temp_labels[0]))
