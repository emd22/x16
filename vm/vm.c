#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define VM_FLAG_HALT 0x01

#define OP_BASE_PUSH 1
#define OP_BASE_POP  2
#define OP_BASE_ADD  3

#define OP_NOP   (0x00)

#define OP_PUSH  ((OP_BASE_PUSH << 4) | 0x00)
#define OP_PUSHI ((OP_BASE_PUSH << 4) | 0x01)

#define OP_POP   ((OP_BASE_POP << 4)  | 0x00)

#define OP_ADD   ((OP_BASE_ADD << 4)  | 0x00)
#define OP_ADDI  ((OP_BASE_ADD << 4)  | 0x01)

#define OP_SYS   0x04

typedef uint16_t vm_register_t;

typedef struct {
    vm_register_t x0, x1, x2, x3;
    vm_register_t sp, bp, pc;
} vm_register_file_t;

typedef struct {
    uint8_t *memory;
    uint16_t memory_size;
    vm_register_file_t regs;
    uint8_t flags;
} vm_t;

vm_t vm_new(uint16_t memory_size) {
    vm_t vm;
    memset(&vm, 0, sizeof(vm_t));

    vm.memory_size = memory_size;
    vm.memory = calloc(1, memory_size);

    return vm;
}

uint16_t *vm_register_from_index(vm_t *vm, int index) {
    switch (index) {
        case 0:
            return NULL;
        case 1:
            return &vm->regs.x0;
        case 2:
            return &vm->regs.x1;
        case 3:
            return &vm->regs.x2;
        case 4:
            return &vm->regs.x3;
        case 5:
            return &vm->regs.sp;
        case 6:
            return &vm->regs.bp;
        case 7:
            return &vm->regs.pc;
        default:;
    }
    return NULL;
}

void vm_load_program(vm_t *vm, uint16_t addr, uint8_t *program, uint16_t program_size) {
    memcpy(vm->memory + addr, program, program_size);
}

uint8_t vm_fetch8(vm_t *vm) {
    return vm->memory[vm->regs.bp + vm->regs.pc++];
}

uint16_t vm_fetch16(vm_t *vm) {
    return ((vm_fetch8(vm) << 8) | vm_fetch8(vm));
}

uint8_t vm_pop8(vm_t *vm) {
    uint8_t value = vm->memory[vm->regs.sp];
    vm->regs.sp--;
    return value;
}

uint16_t vm_pop16(vm_t *vm) {
    // remember, popping reverses the byte order!
    return ((vm_pop8(vm) << 8) | vm_pop8(vm));
}

void vm_op_pushi(vm_t *vm) {
    vm->memory[vm->regs.sp++] = vm_fetch8(vm);
    vm->memory[vm->regs.sp++] = vm_fetch8(vm);
}

void vm_op_pop(vm_t *vm) {
    int ri = vm_fetch8(vm) & 0x0F;

    uint16_t *reg = vm_register_from_index(vm, ri);
    if (reg == NULL) {
        printf("Invalid register %d\n", ri);
        return;
    }

    (*reg) = vm_pop16(vm);
}

void vm_op_addi(vm_t *vm) {
    uint16_t imm = vm_fetch16(vm);

    int ri = vm_fetch8(vm) & 0x0F;

    uint16_t *reg = vm_register_from_index(vm, ri);
    if (reg == NULL) {
        printf("Invalid register %d\n", ri);
        return;
    }

    (*reg) += imm;
}

void vm_op_sys(vm_t *vm) {
    const uint8_t sys = vm_fetch8(vm);

    switch(sys) {
        case 0x00:
            vm->flags |= VM_FLAG_HALT;
            break;
        default:;
    }
}

void vm_print_debug(vm_t *vm) {
    printf(
            "[ x0: 0x%02X x1: 0x%02X x2: 0x%02X x3: 0x%02X "
            ":: sp: 0x%02X bp: 0x%02X pc: 0x%02X]\n",
            vm->regs.x0,
            vm->regs.x1,
            vm->regs.x2,
            vm->regs.x3,
            vm->regs.sp,
            vm->regs.bp,
            vm->regs.pc
    );
}

void vm_step(vm_t *vm) {
    vm_print_debug(vm);

    uint8_t opcode = vm_fetch8(vm);

    switch (opcode) {
        case OP_NOP:
            return;

        case OP_PUSH:
            break;

        case OP_PUSHI:
            vm_op_pushi(vm);
            break;

        case OP_POP:
            vm_op_pop(vm);
            break;

        case OP_ADDI:
            vm_op_addi(vm);
            break;

        case OP_SYS:
            vm_op_sys(vm);
            break;

        default:
            printf("Error: garbage value [0x%02X] in opcode stream\n", opcode);
            break;
    }
}

void vm_run(vm_t *vm) {
    while (!(vm->flags & VM_FLAG_HALT)) {
        if (vm->regs.pc >= vm->memory_size) {
            break;
        }
        vm_step(vm);
    }
}

void vm_destroy(vm_t *vm) {
    free(vm->memory);
}

uint8_t *load_program(char *filename, uint16_t *size) {
    FILE *fp = fopen(filename, "rb");
    if (fp == NULL) {
        fprintf(stderr, "Error: cannot find executable to load!\n");
        exit(1);
    }

    // get the file's size
    fseek(fp, 0, SEEK_END);
    uint32_t file_size = ftell(fp);
    rewind(fp);

    // create a buffer and read into it
    uint8_t *buffer = malloc(file_size);
    fread(buffer, 1, file_size, fp);

    (*size) = file_size;

    return buffer;
}

int main(int argc, char *argv[]) {
    vm_t vm = vm_new(0xFFF0);
    // set up our stack
    vm.regs.sp = 0x5000;

    uint16_t program_size;
    uint8_t *program = load_program("../demo.bin", &program_size);
    // load our program into the vm
    vm_load_program(&vm, 0x00, program, program_size);

    free(program);

    // run the vm!
    vm_run(&vm);

    vm_destroy(&vm);

    return 0;
}
