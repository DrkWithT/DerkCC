"""
    test_lexer.py\n
    Added by DrkWithT (Derek Tan) on 12/20/24
"""

import unittest
import DerkCC.DCCStages.lexer as pycc_lexer

PyCCToken = pycc_lexer.TokenType

class LexerTester(unittest.TestCase):
    def test_sample_1(self):
        tokenizer = pycc_lexer.Lexer()
        test_ok = True

        with open('./c_samples/test_01.c') as source_1:
            temp_token = None
            tokenizer.use_source(source_1.read())

            while True:
                temp_token = tokenizer.lex_next()

                if temp_token is None:
                    break

                if temp_token[2] == PyCCToken.UNKNOWN:
                    print(f'Invalid token: {temp_token}')
                    test_ok = False
                    break

        self.assertTrue(test_ok)
    
    def test_sample_2(self):
        tokenizer = pycc_lexer.Lexer()
        test_ok = True

        with open('./c_samples/test_02.c') as source_2:
            tokenizer.use_source(source_2.read())

            while True:
                temp = tokenizer.lex_next()

                if temp is None:
                    break

                if temp[2] == PyCCToken.UNKNOWN:
                    print(f'Invalid token found: {temp}')
                    test_ok = False
                    break

        self.assertTrue(test_ok)
    
    def test_sample_3(self):
        tokenizer = pycc_lexer.Lexer()
        test_ok = True

        with open('./c_samples/test_03.c') as source_3:
            tokenizer.use_source(source_3.read())

            while True:
                temp = tokenizer.lex_next()

                if temp is None:
                    break

                if temp[2] == PyCCToken.UNKNOWN:
                    print(f'Invalid token found: {temp}')
                    test_ok = False
                    break

        self.assertTrue(test_ok)

    def test_sample_4(self):
        tokenizer = pycc_lexer.Lexer()
        test_ok = True

        with open('./c_samples/test_04.c') as source_4:
            tokenizer.use_source(source_4.read())

            while True:
                temp = tokenizer.lex_next()

                if temp is None:
                    break

                if temp[2] == PyCCToken.UNKNOWN:
                    print(f'Invalid token found: {temp}')
                    test_ok = False
                    break

        self.assertTrue(test_ok)

if __name__ == '__main__':
    unittest.main()
