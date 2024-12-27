"""
    test_parser.py\n
    Added by DrkWithT (Derek Tan)\n
    Tests the parser for my C subset.\n
    TODO I should add more complex tests?
"""

import unittest
import pyCC.pyCmp.parser as pycc_parser

class ParserTester(unittest.TestCase):
    def test_parse_1(self):
        parser = pycc_parser.Parser()
        
        with open('./c_samples/test_01.c') as source_1:
            parser.use_source(source_1.read())

            ast_ok, ast_1 = parser.parse_all()

            print(ast_1)

            self.assertTrue(ast_ok and len(ast_1) > 0)

    def test_parse_2(self):
        parser = pycc_parser.Parser()

        with open('./c_samples/test_02.c') as source_2:
            parser.use_source(source_2.read())

            ast_ok, ast_2 = parser.parse_all()

            print(ast_2)

            self.assertTrue(ast_ok and len(ast_2) > 0)
    
    def test_parse_3(self):
        parser = pycc_parser.Parser()
        
        with open('./c_samples/test_03.c') as source_3:
            parser.use_source(source_3.read())

            ast_ok, ast_3 = parser.parse_all()

            print(ast_3)

            self.assertTrue(ast_ok and len(ast_3) > 0)
    
    def test_parse_4(self):
        parser = pycc_parser.Parser()
        
        with open('./c_samples/test_04.c') as source_4:
            parser.use_source(source_4.read())

            ast_ok, ast_4 = parser.parse_all()

            print(ast_4)

            self.assertTrue(ast_ok and len(ast_4) > 0)

if __name__ == '__main__':
    unittest.main()
