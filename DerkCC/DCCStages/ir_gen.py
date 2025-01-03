"""
    ir_gen.py\n
    By DrkWithT\n
    Defines AST to IR converter.\n
    TODO add type deduction for every AST name... a numeric result has the type of its operands??
"""

from DerkCC.DCCStages.ast_visitor import ASTVisitor
from DerkCC.DCCStages.lexer import TokenType
import DerkCC.DCCStages.ast_nodes as ast
import DerkCC.DCCStages.semantics as sem
import DerkCC.DCCStages.ir_types as ir_types

## Utility types ##

# NOTE models a function-local: datatype, ir_address, is_param
LocalRecord = tuple[ast.DataType, str, bool]

# NOTE models important function info, specifically all its locals
FuncInfo = list[LocalRecord]

# NOTE models all function info entries
FuncInfoTable = dict[str, FuncInfo]

## IR Generator ##

class IREmitter(ASTVisitor):
    AddrUsageTable = dict[str, bool] # NOTE format is "a{num}": bool.

    sem_table: sem.SemanticsTable = None
    addr_table: AddrUsageTable = None
    name_to_addr_table: dict = None
    jump_label_i: int = None
    temp_exits: list[str] = None
    temp_returns: list[str] = None

    curr_func_name: str
    funcs: FuncInfoTable
    results: ir_types.StepList = None

    def __init__(self, sem_info: sem.SemanticsTable):
        self.sem_table = sem_info
        self.addr_table = {
            "A": False, # NOTE True => used!
            "B": False,
            "C": False
        }
        self.name_to_addr_table = {}
        self.jump_label_i = 0
        self.temp_exits = []
        self.temp_returns = []
        self.curr_func_name = None
        self.funcs = FuncInfoTable()
        self.results = []

    def release_all_addrs(self):
        for addr in self.addr_table:
            self.addr_table[addr] = False

        self.name_to_addr_table.clear()

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
            Generates the next usable IR address to store an intermediate value if no candidates exist... but a used address can become unused after use for other operations. This logic basically uses memoization of IR addresses. \n
            * If a reserved register is available AND not for a return result, use the next one.
            * If not, use an existing temporary register if available.
            * Finally, use a new temporary register if no existing ones are available.
        """
        # pool of at least 1 guaranteed free address...
        candidates = self.get_available_addrs()

        for addr in candidates:
            if self.addr_table.get(addr) != True and addr not in self.temp_returns:
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

    def record_func_name(self, fn_name: str):
        self.funcs[fn_name] = []

    def register_func_local(self, fn_name: str, local_type: ast.DataType, local_ir_name: str, is_param: bool):
        if local_type != ast.DataType.UNKNOWN:
            self.funcs[fn_name].append((local_type, local_ir_name, is_param))

    def get_func_infos(self) -> FuncInfoTable:
        return self.funcs

    def gen_ir_from_ast(self, ast: list[ast.Stmt]):
        for stmt in ast:
            stmt.accept_visitor(self)

        return self.results

    def generate_normal_jump(self, target_label: str, expr: ast.Expr):
        # NOTE the 3 NOPs for ASSIGN, AND, OR will be handled by caller code instead...
        expr_op = ir_types.AST_OP_IR_MATCHES.get(expr.get_op_type().name)
        temp = self.allocate_addr()
        op_arity = expr.get_op_arity()

        if op_arity == ast.OpArity.BINARY:
            lhs_temp = expr.get_lhs().accept_visitor(self)
            rhs_temp = expr.get_rhs().accept_visitor(self)
            self.results.append(ir_types.IRAssign(temp, expr_op, lhs_temp, rhs_temp))
            self.results.append(ir_types.IRJumpIf(target_label, ir_types.IROp.COMPARE_NEQ, 0, temp))
            self.toggle_addr_usage(rhs_temp)
            self.toggle_addr_usage(lhs_temp)
        elif op_arity == ast.OpArity.UNARY:
            inner_temp = expr.get_inner().accept_visitor()
            self.results.append(ir_types.IRAssign(temp, expr_op, inner_temp, None))
            self.results.append(ir_types.IRJumpIf(target_label, ir_types.IROp.COMPARE_NEQ, 0, temp))
            self.toggle_addr_usage(inner_temp)

        self.toggle_addr_usage(temp)

    def generate_inverse_jump(self, target_label: str, expr: ast.Expr):
        op = expr.get_op_type()
        inverse_op = ir_types.AST_OP_IR_INVERSES.get(op.name) or ir_types.IROp.NOP
        op_arity = expr.get_op_arity()

        if inverse_op != ir_types.IROp.NOP:
            lhs_temp = expr.get_lhs().accept_visitor(self)
            rhs_temp = expr.get_rhs().accept_visitor(self)

            self.results.append(ir_types.IRJumpIf(target_label, inverse_op, lhs_temp, rhs_temp))
            self.toggle_addr_usage(rhs_temp)
            self.toggle_addr_usage(lhs_temp)
        elif op_arity == ast.OpArity.BINARY:
            temp = self.allocate_addr()
            lhs_temp = expr.get_lhs().accept_visitor(self)
            rhs_temp = expr.get_rhs().accept_visitor(self)

            self.results.append(ir_types.IRAssign(temp, op, lhs_temp, rhs_temp))
            self.results.append(ir_types.IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, temp))
            self.toggle_addr_usage(temp)
            self.toggle_addr_usage(rhs_temp)
            self.toggle_addr_usage(lhs_temp)
        elif op_arity == ast.OpArity.UNARY:
            inner_temp = expr.get_inner().accept_visitor(self)
            temp = self.allocate_addr()
            self.results.append(ir_types.IRAssign(temp, op, inner_temp, None))
            self.results.append(ir_types.IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, inner_temp))
            self.toggle_addr_usage(temp)
            self.toggle_addr_usage(inner_temp)
        elif op_arity == ast.OpArity.NOTHING:
            temp = expr.accept_visitor(self)
            self.results.append(ir_types.IRJumpIf(target_label, ir_types.IROp.COMPARE_EQ, 0, temp))
            self.toggle_addr_usage(temp)

    def visit_literal(self, node: ast.Expr) -> str | int:
        # NOTE literal_token: Literal.LiteralData & literal_arrtype: Literal.ArrayType
        literal_token, literal_arrtype = node.get_data()

        if literal_token is not None:
            # TODO use allocation of IR address...
            lexeme: str = literal_token[0]
            raw_value = 0

            if literal_token[2] == TokenType.LITERAL_INT:
                raw_value = int(lexeme)
                return raw_value
            elif literal_token[2] == TokenType.LITERAL_CHAR:
                raw_value = ord(lexeme[0])
                return raw_value
            elif literal_token[2] == TokenType.IDENTIFIER:
                value_addr = self.name_to_addr_table.get(lexeme)
                return value_addr
        elif literal_arrtype is not None:
            # TODO implement array handling... allocate N addresses where N = arr.length!
            pass

    def visit_unary(self, node: ast.Expr):
        src_item: str | int = node.get_inner().accept_visitor(self)
        op = node.get_op_type()
        dest_addr = self.allocate_addr()

        if op != ast.OpType.OP_NEG:
            return
        
        if type(src_item) == str:
            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NEGATE, src_item, None))
            self.toggle_addr_usage(src_item)
            return dest_addr
        else:
            return -src_item

    def visit_binary(self, node: ast.Expr):
        expr_lhs: ast.Expr = node.get_lhs()
        expr_rhs: ast.Expr = node.get_rhs()
        op = node.get_op_type()
        dest_addr = None

        if op == ast.OpType.OP_LOGIC_AND:
            falsy_label = self.generate_next_label()
            truthy_label = self.generate_next_label()
            dest_addr = self.allocate_addr()

            self.generate_inverse_jump(falsy_label, expr_lhs)
            self.generate_inverse_jump(falsy_label, expr_rhs)
            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NOP, 1, None))
            self.results.append(ir_types.IRJump(truthy_label))

            self.results.append(ir_types.IRLabel(falsy_label))
            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NOP, 0, None))
            self.results.append(ir_types.IRLabel(truthy_label))
        elif op == ast.OpType.OP_LOGIC_OR:
            falsy_label = self.generate_next_label()
            truthy_label = self.generate_next_label()
            skippy_label = self.generate_next_label()
            dest_addr = self.allocate_addr()

            self.generate_normal_jump(truthy_label, expr_lhs)
            self.generate_normal_jump(truthy_label, expr_rhs)
            self.results.append(ir_types.IRJump(falsy_label))

            self.results.append(ir_types.IRLabel(truthy_label))
            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NOP, 1, None))
            self.results.append(ir_types.IRJump(skippy_label))

            self.results.append(ir_types.IRLabel(falsy_label))
            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NOP, 0, None))
            self.results.append(ir_types.IRLabel(skippy_label))
        elif op != ast.OpType.OP_ASSIGN:
            arg0_item = expr_lhs.accept_visitor(self)
            arg1_item = expr_rhs.accept_visitor(self)
            dest_addr = self.allocate_addr()

            self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp(op.value), arg0_item, arg1_item))

            self.toggle_addr_usage(arg1_item)
            self.toggle_addr_usage(arg0_item)
        else:
            dest_addr = expr_lhs.accept_visitor(self)
            value_item = expr_rhs.accept_visitor(self)

            if value_item is not None:
                self.results.append(ir_types.IRAssign(dest_addr, ir_types.IROp.NOP, value_item, None))
                self.toggle_addr_usage(value_item)

        return dest_addr

    def visit_call(self, node: ast.Expr):
        func_name: str = node.get_name()
        func_retype: ast.DataType = self.sem_table.get('.global').get(func_name).data_type
        func_argv: ast.Call.ArgList = node.get_args()

        for arg in func_argv:
            arg_type = arg.deduce_early_type()

            if arg.get_op_type() == ast.OpType.OP_NONE:
                # NOTE either check lexeme of literal for its value...
                temp_lexeme: str = arg.get_data()[0][0]
                temp_value = int(temp_lexeme) if temp_lexeme[0] != '\'' else ord(temp_lexeme[1])
                self.results.append(ir_types.IRPushArg(temp_value, True, arg_type))
            else:
                # ... or just process a temporary value from an arg. expr.
                temp_arg_addr: str = arg.accept_visitor(self)
                self.results.append(ir_types.IRPushArg(temp_arg_addr, False, arg_type))

        self.results.append(ir_types.IRCallFunc(func_name))

        if func_retype != ast.DataType.UNKNOWN and func_retype != ast.DataType.VOID:
            result_addr = self.allocate_addr()
            self.results.append(ir_types.IRStoreYield(result_addr))
            return result_addr

    def visit_variable_decl(self, node: ast.Stmt):
        var_addr = self.allocate_addr()
        self.register_func_local(self.curr_func_name, node.get_type(), var_addr, False)

        self.name_to_addr_table[node.get_name()] = var_addr
        rhs_addr: str = node.get_rhs().accept_visitor(self)
        self.results.append(ir_types.IRAssign(var_addr, ir_types.IROp.NOP, rhs_addr, None))
        return var_addr

    def visit_block(self, node: ast.Stmt):
        for stmt in node.get_stmts():
            stmt.accept_visitor(self)

    def visit_function_decl(self, node: ast.Stmt):
        func_name: str = node.get_name()
        func_param_v: ast.ParamList = node.get_params()
        self.curr_func_name = func_name
        self.record_func_name(func_name)

        self.results.append(ir_types.IRLabel(func_name))

        for param in func_param_v:
            param_addr = self.allocate_addr()
            self.register_func_local(func_name, param[0], param_addr, True)

            self.name_to_addr_table[param[1]] = param_addr
            self.results.append(ir_types.IRLoadParam(param_addr))

        ret_label = self.generate_next_label()
        self.temp_exits.append(ret_label)

        node.get_body().accept_visitor(self)

        self.results.append(ir_types.IRLabel(ret_label))
        self.results.append(ir_types.IRReturn(self.temp_returns.pop()))

        self.curr_func_name = None
        self.temp_exits.clear()
        self.release_all_addrs()

    def visit_expr_stmt(self, node: ast.Stmt):
        op = node.get_inner().get_op_type()

        if op == ast.OpType.OP_CALL or op == ast.OpType.OP_ASSIGN:
            node.get_inner().accept_visitor(self)

    def visit_if(self, node: ast.Stmt):
        truthy_body: ast.Stmt = node.get_if_body()
        falsy_body: ast.Stmt = node.get_alt_body()
        falsy_label = self.generate_next_label()

        cond_addr = node.get_conditions().accept_visitor(self)
        self.results.append(ir_types.IRJumpIf(falsy_label, ir_types.IROp.COMPARE_EQ, 0, cond_addr))

        truthy_body.accept_visitor(self)

        if falsy_body is not None:
            truthy_label = self.generate_next_label()

            self.results.append(ir_types.IRJump(truthy_label))
            self.results.append(ir_types.IRLabel(falsy_label))
            falsy_body.accept_visitor(self)
            self.results.append(ir_types.IRLabel(truthy_label))
        else:
            self.results.append(ir_types.IRLabel(falsy_label))

        self.toggle_addr_usage(cond_addr)

    def visit_return(self, node: ast.Stmt):
        result_dest = self.allocate_addr()
        result_expr = node.get_result_expr()
        result_src = result_expr.accept_visitor(self)
        self.temp_returns.append(result_dest)
        result_type = result_expr.deduce_early_type()

        if result_type == ast.DataType.UNKNOWN and type(result_expr) == ast.Call:
            result_type = self.sem_table.get('.global').get(result_expr.get_name()).data_type

        self.results.append(ir_types.IRAssign(result_dest, ir_types.IROp.NOP, result_src, None))
        self.register_func_local(self.curr_func_name, result_type, result_dest, False)
        self.results.append(ir_types.IRJump(self.temp_exits[0]))
        print(self.funcs.get(self.curr_func_name)) # debug
