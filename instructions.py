# Instruction format
OPCODE_BITS = 3
REG_BITS = 3
I_TYPE_IMMEDIATE_BITS = 7
J_TYPE_IMMEDIATE_BITS = 13

ADDRESS_INCREMENT = 2


# Basic instruction, all fields except opcode are zero.
class Instruction:
    def __init__(self, name, opcode):
        self.name = name
        self.opcode = opcode

    def __repr__(self):
        return self.name

    def to_machine_code(self, address, *args):
        return self.opcode << (16 - OPCODE_BITS)


class RType(Instruction):
    def __init__(self, name, opcode, funct):
        super().__init__(name, opcode)
        self.funct = funct

    def to_machine_code(self, address, *args):
        rd = args[0]
        rs = args[1]
        rt = args[2]
        assert (self.funct < 32)
        return (self.opcode << (16 - OPCODE_BITS)) \
               + (rs.address << (16 - OPCODE_BITS - REG_BITS)) \
               + (rt.address << (16 - OPCODE_BITS - 2 * REG_BITS)) \
               + (rd.address << (16 - OPCODE_BITS - 3 * REG_BITS)) \
               + self.funct


class IType(Instruction):
    def to_machine_code(self, address, *args):
        rt = args[0]
        rs = args[1]
        imm = args[2]
        assert(128 > imm > -129)
        imm = imm & 0b1111111  # 7 bit immediate
        return (self.opcode << (16 - OPCODE_BITS)) \
               + (rs.address << (16 - OPCODE_BITS - REG_BITS)) \
               + (rt.address << (16 - OPCODE_BITS - 2 * REG_BITS)) \
               + imm


class Branch(IType):
    def to_machine_code(self, address, *args):
        rt = args[0]
        rs = args[1]
        target_addr = args[2]
        imm = (target_addr - address - ADDRESS_INCREMENT) // ADDRESS_INCREMENT
        assert(128 > imm > -129)
        imm = imm & 0b1111111  # 7 bit immediate
        return (self.opcode << (16 - OPCODE_BITS)) \
               + (rs.address << (16 - OPCODE_BITS - REG_BITS)) \
               + (rt.address << (16 - OPCODE_BITS - 2 * REG_BITS)) \
               + imm


class JType(Instruction):
    def to_machine_code(self, address, *args):
        imm = args[0]

        return (self.opcode << (16 - OPCODE_BITS)) + imm


# R-type instruction with three register arguments and a function code
r_instructions = [
    RType('add', 0b000, 0b0000),
    RType('sub', 0b000, 0b0001),
    RType('asl', 0b000, 0b0010),
    RType('asr', 0b000, 0b0011),
    RType('and', 0b000, 0b0110),
    RType('nor', 0b000, 0b0111),
    RType('or', 0b000, 0b1000),
    RType('slt', 0b000, 0b1001),
    RType('sll', 0b000, 0b1010),
    RType('srl', 0b000, 0b1011),
    RType('xor', 0b000, 0b1100),
]

# R-type with only two register arguments (third register is assumed to be 0)
reduced_r_instructions = [
    RType('asl1', 0b000, 0b0100),
    RType('asr1', 0b000, 0b0101),
]

i_instructions = [
    IType('addi', 0b001),
    Branch('bne', 0b010),
    Branch('blt', 0b011),
    IType('lw', 0b100),
    IType('sw', 0b101),
]

j_instructions = [
    JType('j', 0b110)
]

nop_instructions = [
    Instruction('nop', 0b111),
    Instruction('halt', 0b111)
]
