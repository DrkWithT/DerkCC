"""
    test_lexer.py\n
    Added by DrkWithT (Derek Tan) on 12/20/24
"""

import unittest
import pyCC.pyCmp.lexer as pycc_lexer

PyCCToken = pycc_lexer.TokenType

class LexerTester(unittest.TestCase):
    def test_sample_1(self):
        # NOTE ignore spaces though for simplicity.
        expected_token_types = [
            PyCCToken.LINE_COMMENT,
            PyCCToken.LINE_COMMENT,
            PyCCToken.TYPENAME_INT,
            PyCCToken.IDENTIFIER,
            PyCCToken.PAREN_OPEN,
            PyCCToken.PAREN_CLOSE,
            PyCCToken.BRACE_OPEN,
            PyCCToken.TYPENAME_INT,
            PyCCToken.IDENTIFIER,
            PyCCToken.OP_ASSIGN,
            PyCCToken.LITERAL_INT,
            PyCCToken.SEMICOLON,
            PyCCToken.KEYWORD,
            PyCCToken.LITERAL_INT,
            PyCCToken.SEMICOLON,
            PyCCToken.BRACE_CLOSE
        ]

        tokenizer = pycc_lexer.Lexer()
        result_tags = [] # NOTE holds resulting lexer's token types, must check against expected sequence...
        test_ok = True

        with open('./c_samples/test_01.c') as source_1:
            temp_token = None
            tokenizer.use_source(source_1.read())

            while True:
                temp_token = tokenizer.lex_next()

                if temp_token is None:
                    test_ok = (result_tags == expected_token_types)
                    break

                if temp_token[2] == PyCCToken.SPACING:
                    continue

                if temp_token[2] == PyCCToken.UNKNOWN:
                    print(f'Invalid token: {temp_token}')
                    test_ok = False
                    break

                result_tags.append(temp_token[2])

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
