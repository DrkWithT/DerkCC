"""
    test_ir_gen.py\n
    Added by DrkWithT\n
    Unit testing for IR generator from AST.
"""

import unittest
import pyCC.pyCmp.parser as par
import pyCC.pyCmp.semantics as sem
import pyCC.pyCmp.ir_gen as irgen

def test_impl(file_path: str):
    parser = par.Parser()
    checker = sem.SemanticChecker()

    with open(file_path) as src:
        parser.use_source(src.read())
        ok, ast = parser.parse_all()

        if not ok:
            print(f'Parse failed in {file_path}!')
            return False

        errors = checker.check_ast(ast)

        for err in errors:
            print(f'Semantic Error:\nCulprit symbol: {err[0]}\nScope of {err[1]}\n{err[2]}\n')

        if len(errors) > 0:
            print(f'Semantic validation failed for {file_path}!')
            return False

        ir_result = irgen.IREmitter(checker.eject_semantic_info()).gen_ir_from_ast(ast)

        if len(ir_result) == 0:
            print(f'No IR generated for {file_path}!')
            return False

        print('Generated IR:\n')
        for step in ir_result:
            print(f'{step}\n')

        return True

class IRGenTester(unittest.TestCase):
    # def test_good_1(self):
    #     self.assertTrue(test_impl('./c_samples/test_01.c'))

    # def test_good_2(self):
    #     self.assertTrue(test_impl('./c_samples/test_02.c'))

    # def test_good_3(self):
    #     self.assertTrue(test_impl('./c_samples/test_03.c'))

    # def test_good_4(self):
    #     self.assertTrue(test_impl('./c_samples/test_04.c'))

    def test_good_4a(self):
        self.assertTrue(test_impl('./c_samples/test_04a.c'))
