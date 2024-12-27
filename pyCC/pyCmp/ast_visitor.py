"""
    ASTVisitor.py\n
    TODO implement base class to deal with various AST types...
"""

class ASTVisitor:
    def visit_literal(self, node) -> "any":
        pass

    def visit_unary(self, node) -> "any":
        pass

    def visit_binary(self, node) -> "any":
        pass

    def visit_call(self, node) -> "any":
        pass

    def visit_variable_decl(self, node) -> "any":
        pass

    def visit_block(self, node) -> "any":
        pass

    def visit_function_decl(self, node) -> "any":
        pass

    def visit_expr_stmt(self, node) -> "any":
        pass

    def visit_if(self, node) -> "any":
        pass

    def visit_return(self, node) -> "any":
        pass
