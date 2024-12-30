"""
    test_asm_gen.py\n
    By: DrkWithT\n
    Test simple GAS gen... (there goes my sanity thanks to the ABI rules)
"""

import unittest
import DerkCC.DCCStages.parser as par
import DerkCC.DCCStages.semantics as sem
import DerkCC.DCCStages.ir_gen as irgen
import DerkCC.DCCStages.gas_gen as asmgen

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

        ir_maker = irgen.IREmitter(checker.eject_semantic_info())
        ir_result = ir_maker.gen_ir_from_ast(ast)

        if not ir_result:
            print(f'No IR generated for {file_path}!')
            return False

        print('Generated IR:\n')
        for step in ir_result:
            print(f'{step}')

        asm_result = asmgen.GASEmitter(ir_maker.get_func_infos()).emit_all(ir_result)

        if not asm_result:
            print(f'No ASM generated for {file_path}!')
            return False

        print('Generated ASM:\n')
        for asm_line in asm_result:
            print(asm_line)

        return True

class GASEmitterTester(unittest.TestCase):
    # def test_good_1(self):
    #     self.assertTrue(test_impl('./c_samples/test_01.c'))

    # def test_good_2(self):
    #     self.assertTrue(test_impl('./c_samples/test_02.c'))

    def test_good_3(self):
        self.assertTrue(test_impl('./c_samples/test_03.c'))

    # def test_good_4a(self):
    #     self.assertTrue(test_impl('./c_samples/test_04a.c'))

if __name__ == '__main__':
    unittest.main()
