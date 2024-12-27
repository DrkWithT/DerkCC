# pyCC (fork by DrkWithT)
A basic C compiler written in Python. Will support a microscopic part of C99 specified in [Subset Notes](./Grammar.md).

## Usage (TODO):
```sh
python3 ./pyCC/pyCC.py -S file.c
```

## TODO:
- [x] Test and fix parser!
- [x] Fix semantic analyzer for now!
- [ ] Create IR generator by the ASTVisitor!
- [ ] Create ASM generator to convert from IR.
- [ ] Compare ASM output with GCC -std=c99 -S file.c?
