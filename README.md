# PyAssembler
An assembler for a MIPS-like architecture written in Python

## Usage:
1. Download/clone the repository
2. run `python assembler.py [-o OUTFILE] INFILE`
3. The assembled machine code will be written to OUTFILE

## Modifying for a different assembly language:
- Change the registers in registers.py to match your architechture
- In instructions.py, change `OPCODE_BITS, REG_BITS`, `I_TYPE_IMMEDIATE_BITS`, and `J_TYPE_IMMEDIATE_BITS` to match your addressing modes
- Change the instructions in instructions.py to match your architechture
- Modify the functions in instructions.py that generate machine code to match your architecture. These are the `to_machine_code` function in each different instruction type class.
- Make sure the jump/branch address calculation works correctly for your architecture.
