# Grammar

### Notes:
 - Supported subset of C is a microscopic part of C99.

### Planned Features:
 1. Simple types of variables e.g `char, int`.
 2. Simple arithmetic, specifically MDAS
 3. Basic control flow
 4. Function calls
 5. Simple arrays e.g `char[N], int[N]`
 6. Simple structs
 7. Type qualifiers
    - `const`?
 8. Simple 1-D arrays
    - Example: `int nums[4] = {1, 2, 3, 4};`
 9. Pointers
    - Declarations and defererencing?
 10. Typedefs

### Rules:
```bnf
<literal> ::= <char> | <integer> | "(" <expr> ")" | <call-or-name>
<call-or-name> ::= <identifier> (<args>)?
<unary> ::= "-"? <literal>
<factor> ::= <unary> (("*" | "/") <unary>)*
<term> ::= <factor> (("+" | "-") <factor>)*
<comparison> ::= <term> (("<" | "<=" | ">" | ">=") <term>)*
<equality> ::= <comparison> (("==" | "!=") <comparison>)*
<and> ::= <equality> ("&&" <equality>)*
<or> ::= <and> ("||" <and>)*
<expr> ::= <assign> | <or>
<assign> ::= <identifier> "=" <expr>

; NOTE: call is expr-stmt!

<declaration> ::= <variable> | <function>
<variable> ::= <typename> <identifier> "=" <expr> ";"
<function> ::= <typename> <identifier> <params> <block>
<block> ::= "{" (<nestable-stmt>)* "}"
<nestable-stmt> ::= <if> | <return> | <variable> | <expr-stmt>
<expr-stmt> ::= <expr> ";"
<params> ::= "(" (<typename> <identifier> ",")* ")"
<args> ::= "(" (<expr> ",")* ")"
<if> ::= "if" "(" <expr> ")" <block> <else>?
<else> ::= "else" <block>
<return> ::= "return" <expr> ";"
<program> ::= (<declaration>)+
```