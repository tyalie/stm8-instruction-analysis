# Analysis script for STM8 opcodes

This is a small and simple script that I used to analyze the STM8 opcodes as
described in [stm8-binutils-gdb][binutils] (see struct `stm8_opcodes` in `opcodes/stm8-opc.c`).
It was mainly used to allow us to discuss possible opcode classifications for the
STM8 ISA that could then be used to reduce the overhead when implementing all
instructions for our [STM8 LLVM backend][stm8-llvm].

> [!NOTE]
> The issues are open for discussions. So if you have suggestions, please write me ^^

## Output

The script has the following output when using the commit 07d863397.

```
================
Distribution of how many different opcodes a single asm mnemonic has

1:
    nop, break, callr, ccf, divw, exgw, halt, int, iret, 
    jra, jrc, jreq, jrf, jrh, jrih, jril, jrm, jrmi, 
    jrnc, jrne, jrnh, jrnm, jrnv, jrpl, jrsge, jrsgt, jrsle, 
    jrslt, jrt, jruge, jrugt, jrule, jrult, jrv, rcf, ret, 
    retf, rim, rvf, scf, sim, trap, wfe, wfi, 
2:
    callf, clrw, cplw, decw, div, incw, jpf, mul, negw, 
    popw, pushw, rlcw, rlwa, rrcw, rrwa, sllw, slaw, sraw, 
    srlw, swapw, tnzw, 
3:
    exg, mov, pop, 
4:
    push, 
6:
    subw, 
7:
    addw, 
8:
    bccm, bcpl, bres, bset, btjf, btjt, 
12:
    call, jp, ldf, 
15:
    adc, add, and, bcp, clr, cp, cpl, dec, inc, 
    neg, or, rlc, rrc, sbc, sll, sla, sra, srl, 
    swap, tnz, xor, 
16:
    sub, 
19:
    cpw, 
37:
    ld, 
44:
    ldw, 

================
There are 26 different opcode argument tuples
   - 
   - BYTE
   - SHORTMEM
   - LONGMEM
   - SHORTOFF_X
   - LONGOFF_X
   - SHORTOFF_Y
   - LONGOFF_Y
   - SHORTOFF_SP
   - SHORTPTRW
   - LONGPTRW
   - SHORTPTRW_X
   - LONGPTRW_X
   - SHORTPTRW_Y
   - WORD
   - LONGMEM, PCREL
   - EXTMEM
   - LONGPTRE
   - PCREL
   - EXTOFF_X
   - EXTOFF_Y
   - LONGPTRE_X
   - LONGPTRE_Y
   - LONGMEM, BYTE
   - SHORTMEM, SHORTMEM
   - LONGMEM, LONGMEM

================
The following mnemonic groups exist. The criterias have been:
  - same amount of opcodes / argument types per mnemonic
  - for each opcode & argument from a mnemonic there is a matching pair
    in the other mnemonic where the opcode just has a constant offset

Group 1:
    callr, jra, jrc, jreq, jrf, jrh, jrih, jril, jrm, 
    jrmi, jrnc, jrne, jrnh, jrnm, jrnv, jrpl, jrsge, jrsgt, 
    jrsle, jrslt, jrt, jruge, jrugt, jrule, jrult, jrv, 
Group 2:
    adc, add, and, bcp, cp, or, sbc, xor, 
Group 3:
    clrw, cplw, decw, incw, negw, popw, pushw, rlcw, rrcw, 
    sllw, slaw, sraw, srlw, swapw, tnzw, 
Group 4:
    nop, break, ccf, halt, iret, rcf, ret, retf, rim, 
    rvf, scf, sim, trap, wfe, wfi, 
Group 5:
    div, mul, rlwa, rrwa, 
Group 6:
    clr, cpl, dec, inc, neg, rlc, rrc, sll, sla, 
    sra, srl, swap, tnz, 
Group 7:
    btjf, btjt, 
Group 8:
    divw, exgw, 
Group 9:
    call, jp, 
Group 10:
    callf, jpf, 
Group 11:
    bccm, bcpl, bres, bset, 

unique:
    sub, ldf, int, pop, subw, push, ldw, addw, ld, 
    mov, cpw, exg, 
```

## Requirements

The script currently uses [tree sitter][tree-sitter] to build the opcode database
from the above-mentioned struct.

[binutils]: github.com/tyalie/stm8-binutils-gdb
[stm8-llvm]: github.com/nrdmn/llvm-project
[tree-sitter]: https://github.com/tree-sitter/tree-sitter
