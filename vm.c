#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define VM_FLAG_HALT  0x01
#define VM_FLAG_STEP_DEBUG 0x02

#define VM_FLAG_LESS_THAN 0x40
#define VM_FLAG_GREATER_THAN 0x80

#define OP_BASE_PUSH    1
#define OP_BASE_POP     2
#define OP_BASE_ADD     3
#define OP_SYS          4
#define OP_BASE_BRANCH  5
#define OP_BASE_COMPARE 6
#define OP_BASE_AND     7
#define OP_BASE_OR      8

#define OP_NOP   (0x00)

#define OP_PUSH  ((OP_BASE_PUSH << 4) | 0x00)
#define OP_PUSHI ((OP_BASE_PUSH << 4) | 0x01)

#define OP_POP   ((OP_BASE_POP << 4)  | 0x00)

#define OP_ADD   ((OP_BASE_ADD << 4)  | 0x00)
#define OP_ADDI  ((OP_BASE_ADD << 4)  | 0x01)

#define OP_BRANCH               ((OP_BASE_BRANCH << 4) | 0x00)
#define OP_BRANCH_LESS_THAN     ((OP_BASE_BRANCH << 4) | 0x01)
#define OP_BRANCH_GREATER_THAN  ((OP_BASE_BRANCH << 4) | 0x02)
#define OP_BRANCH_EQUAL_TO      ((OP_BASE_BRANCH << 4) | 0x03)
#define OP_BRANCH_NOT_EQUAL_TO  ((OP_BASE_BRANCH << 4) | 0x04)

#define OP_CMP    ((OP_BASE_COMPARE << 4) | 0x00)
#define OP_CMPI   ((OP_BASE_COMPARE << 4) | 0x01)

#define OP_ANDI   ((OP_BASE_AND << 4) | 0x01)
#define OP_ORI    ((OP_BASE_OR << 4) | 0x01)

#define VM_GREATER_THAN(vm) (vm->flags & VM_FLAG_GREATER_THAN)
#define VM_LESS_THAN(vm) (vm->flags & VM_FLAG_LESS_THAN)
#define VM_NOT_EQUAL(vm) (VM_GREATER_THAN(vm) || VM_LESS_THAN(vm))
#define VM_EQUAL(vm) (!VM_NOT_EQUAL(vm))

#define VM_RESET_CMP_FLAGS(vm) (vm->flags &= ~(VM_FLAG_GREATER_THAN | VM_FLAG_LESS_THAN))

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

typedef enum {
    VM_BRANCH_MODE_DIRECT = 0,
    VM_BRANCH_MODE_LESS_THAN = 1,
    VM_BRANCH_MODE_GREATER_THAN = 2,
    VM_BRANCH_MODE_EQUAL_TO = 3,
    VM_BRANCH_MODE_NOT_EQUAL_TO = 4
} vm_branch_mode_t;

typedef enum {
    VM_BITWISE_TYPE_AND = 0,
    VM_BITWISE_TYPE_OR  = 1,
} vm_bitwise_type_t;

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
    uint8_t value = vm->memory[--vm->regs.sp];
    return value;
}

uint16_t vm_pop16(vm_t *vm) {
    return vm_pop8(vm) | ((uint16_t)vm_pop8(vm) << 8);
}

void vm_print_stack(vm_t *vm) {
    printf("Stack: ");
    for (int i = 0x5000; i < vm->regs.sp; i++) {
        printf("%02X ", vm->memory[i]);
    }
    printf("\n");
}

void vm_op_push(vm_t *vm) {
    int ri = vm_fetch8(vm) & 0x0F;

    uint16_t *reg = vm_register_from_index(vm, ri);
    if (reg == NULL) {
        printf("Invalid register %d\n", ri);
        return;
    }
    uint16_t value = *reg;


    vm->memory[vm->regs.sp++] = (value >> 8) & 0xFF;
    vm->memory[vm->regs.sp++] = value & 0xFF;

//    vm_print_stack(vm);
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

//    vm_print_stack(vm);

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
        case 0x01:
            printf("%c", vm->regs.x0 & 0xFF);
            break;
        case 0x02:
            vm->flags ^= VM_FLAG_STEP_DEBUG;
            break;
        default:;
    }
}

void vm_jump_to(vm_t *vm, uint16_t location) {
    // jump to new location
    vm->regs.pc = location;

    // reset compare flags
    VM_RESET_CMP_FLAGS(vm);
}

void vm_op_branch(vm_t *vm, vm_branch_mode_t mode) {
    uint16_t location = vm_fetch16(vm);

    if (mode == VM_BRANCH_MODE_DIRECT) {
        vm_jump_to(vm, location);
    }
    else if (mode == VM_BRANCH_MODE_LESS_THAN && VM_LESS_THAN(vm)) {
        vm_jump_to(vm, location);
    }
    else if (mode == VM_BRANCH_MODE_GREATER_THAN && VM_GREATER_THAN(vm)) {
        vm_jump_to(vm, location);
    }
    else if (mode == VM_BRANCH_MODE_EQUAL_TO && VM_EQUAL(vm)) {
        vm_jump_to(vm, location);
    }
    else if (mode == VM_BRANCH_MODE_NOT_EQUAL_TO && VM_NOT_EQUAL(vm)) {
        vm_jump_to(vm, location);
    }
}

void vm_op_cmp(vm_t *vm) {
    int registers = vm_fetch8(vm);

    uint8_t srci = registers >> 4;
    uint8_t desti = registers & 0x0F;

    uint16_t *reg_src = vm_register_from_index(vm, srci);
    uint16_t *reg_dest = vm_register_from_index(vm, desti);
    if (reg_src == NULL || reg_dest == NULL) {
        printf("Invalid register(s) %d, %d\n", srci, desti);
        return;
    }

    VM_RESET_CMP_FLAGS(vm);

    int cmp_value = ((int)(*reg_src)) - (*reg_dest);

    if (cmp_value < 0) {
        vm->flags |= VM_FLAG_LESS_THAN;
    }
    else if (cmp_value > 0) {
        vm->flags |= VM_FLAG_GREATER_THAN;
    }
}

void vm_op_cmpi(vm_t *vm) {
    uint16_t imm = vm_fetch16(vm);

    int ri = vm_fetch8(vm) & 0x0F;

    uint16_t *reg = vm_register_from_index(vm, ri);
    if (reg == NULL) {
        printf("Invalid register %d\n", ri);
        return;
    }

    VM_RESET_CMP_FLAGS(vm);

    int cmp_value = ((int)(*reg)) - imm;

    if (cmp_value < 0) {
        vm->flags |= VM_FLAG_LESS_THAN;
    }
    else if (cmp_value > 0) {
        vm->flags |= VM_FLAG_GREATER_THAN;
    }
}

void vm_op_bitwisei(vm_t *vm, vm_bitwise_type_t type) {
    uint16_t imm = vm_fetch16(vm);

    int ri = vm_fetch8(vm) & 0x0F;

    uint16_t *reg = vm_register_from_index(vm, ri);
    if (reg == NULL) {
        printf("Invalid register %d\n", ri);
        return;
    }

    if (type == VM_BITWISE_TYPE_AND) {
        (*reg) &= imm;
    }
    else if (type == VM_BITWISE_TYPE_OR) {
        (*reg) |= imm;
    }
}

void vm_print_debug(vm_t *vm) {
    printf(
            "[ x0: 0x%04X x1: 0x%04X x2: 0x%04X x3: 0x%04X "
            ":: sp: 0x%04X bp: 0x%04X pc: 0x%04X] || fl:0x%02X\n",
            vm->regs.x0,
            vm->regs.x1,
            vm->regs.x2,
            vm->regs.x3,
            vm->regs.sp,
            vm->regs.bp,
            vm->regs.pc,
            vm->flags
    );
}

void vm_step(vm_t *vm) {
    if (vm->flags == VM_FLAG_STEP_DEBUG) {
        vm_print_debug(vm);
    }

    uint8_t opcode = vm_fetch8(vm);

    switch (opcode) {
        case OP_NOP:
            return;

        case OP_PUSH:
            vm_op_push(vm);
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

        case OP_BRANCH:
            vm_op_branch(vm, VM_BRANCH_MODE_DIRECT);
            break;
        case OP_BRANCH_LESS_THAN:
            vm_op_branch(vm, VM_BRANCH_MODE_LESS_THAN);
            break;
        case OP_BRANCH_GREATER_THAN:
            vm_op_branch(vm, VM_BRANCH_MODE_GREATER_THAN);
            break;
        case OP_BRANCH_EQUAL_TO:
            vm_op_branch(vm, VM_BRANCH_MODE_EQUAL_TO);
            break;
        case OP_BRANCH_NOT_EQUAL_TO:
            vm_op_branch(vm, VM_BRANCH_MODE_NOT_EQUAL_TO);
            break;

        case OP_CMP:
            vm_op_cmp(vm);
            break;

        case OP_CMPI:
            vm_op_cmpi(vm);
            break;

        case OP_ANDI:
            vm_op_bitwisei(vm, VM_BITWISE_TYPE_AND);
            break;

        case OP_ORI:
            vm_op_bitwisei(vm, VM_BITWISE_TYPE_OR);
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
    uint8_t *program = load_program("demos/print/helloworld.bin", &program_size);
    // load our program into the vm
    vm_load_program(&vm, 0x00, program, program_size);

    free(program);

    // run the vm!
    vm_run(&vm);

    vm_destroy(&vm);

    return 0;
}
