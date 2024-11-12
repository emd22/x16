# X16 CPU and Assembler
This is a small project I started working on about a year ago, just to be able to run some small programs and write an assembler.
The assembler is written in Python to make it super fast to write and extend, while the virtual machine is fully written in C for performance.

To assemble a demo, you can run the following commands:
```bash
python3 asm.py demos/hello/helloworld.dS # or any other demo!
./vm --prog demos/hello/helloworld.bin
```

To debug, use the `--debug` or the `--step-delay` flags, or see the `--help` switch for a list of the available commands!
