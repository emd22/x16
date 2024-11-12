# X16 CPU and Assembler
This is a small project I started working on about a year ago, just to be able to run some small programs and write an assembler.
The assembler is written in Python to make it super fast to write and extend, while the virtual machine is fully written in C for performance.

To assemble a demo, you can run the following commands:
```bash
python3 asm.py demos/hello/helloworld.dS # or any other demo!
./vm --prog demos/hello/helloworld.bin
```

To debug, use the `--debug` or the `--step-delay` flags, or see the `--help` switch for a list of the available commands!



## Registers

**x0, x1, x2, x3** &mdash; general purpose registers

**sp** &mdash; stack pointer

**bp** &mdash; base pointer (start of the program)

**pc** &mdash; program counter. current location in program.

## Syscalls
**0x00** &mdash; stop execution

**0x01** &mdash; print first byte of x0 register as character

**0x02** &mdash; toggle step debug (register dump on every step)

**0x03** &mdash; load file from disk

Input:
 - **x0** &mdash; memory address to load into
 - **x1** &mdash; pointer to path of the file

## Instructions

`pushi [imm]`             &mdash; push an immediate value to the stack. always 16 bit

`push [reg]`              &mdash; push a register to the stack. always 16 bit

`pop [reg]`               &mdash; pop a value off the stack into a register

`addi [imm] [reg]`        &mdash; add an immediate value to a register

`add [reg] [reg]`         &mdash; add a register to a register

`sys [imm8]`              &mdash; send a syscall to the cpu


`cmp [reg] [reg]`         &mdash; compare two register values

`cmpi [imm] [reg]`        &mdash; compare the value of a register to an immediate value


`not [reg]`               &mdash; bitwise negate a register

`andi [imm] [reg]`        &mdash; bitwise AND a register with an immediate value

`ori  [imm] [reg]`        &mdash; bitwise OR a register with an immediate value


`b [label]`               &mdash; immediately branch to a label

`blt [label]`             &mdash; branch to a label if a comparison result is a negative number

`bgt [label]`             &mdash; branch to a label if a comparison result is a positive number

`be [label]`              &mdash; branch to a label if a comparison result is zero

`bne [label]`             &mdash; branch to a label if a comparison result is non-zero

## Directives

`.str [string]`           &mdash; encode data into the executable

## Macros

```asm
{# [macro_name] [number of arguments]
    ; instructions here ...

    ;[instruction] #[index of argument]
    ; push #0
    ; or
    ; pop #1
#}
```

for example,

```asm
; exchange the values between two registers
{# xchg 2
    push #0
    mov #1, #0
    pop #1
#}
```

would be used like:

```asm
xchg x1, x2
```

and would result in the code generated as

```asm
push x1
mov x2, x1
pop x2
```
