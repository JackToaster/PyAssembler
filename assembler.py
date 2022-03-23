from instructions import ADDRESS_INCREMENT
from parser import parse_asm, Label, ParserInput

import argparse
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', metavar='INPUT', help='Assembly file to read')
    parser.add_argument('-o', metavar='OUTPUT', help='File to write hexadecimal machine code into')

    args = parser.parse_args()

    asmfile = args.infile
    outfile = args.o

    if outfile is None:
        outfile = Path(asmfile)
        outfile = outfile.with_suffix('.o')

    # First pass: Parse text into syntax tree (not a very impressive tree as assembly has no nesting structure)
    with open(asmfile, 'r') as asmfile:
        asm_text = asmfile.read()
        # print(len(asm_text))
        parse_input = ParserInput(asm_text)
        ast, rem = parse_asm(parse_input)
        # if len(rem.rtext()) > 0:
        #     print('Failed to parse entire file. Remainder: {}'.format(rem.rtext()))

        if ast.error():
            # print(ast)
            parse_input.display_error(ast, 4, 5)
            sys.exit(1)

    # print(ast)

    # Second pass: determine addresses addresses for labels
    address = 0
    label_addresses = {}
    for item in ast.value:
        if isinstance(item.value, Label):  # found label, assign value for the following instruction
            if item.value not in label_addresses.keys():
                label_addresses[item.value] = address
            else:
                print('Error: Label {} defined more than once'.format(item.value.name))
                sys.exit(1)
        elif hasattr(item.value, '__iter__'):  # Found instruction, increment address
            address += ADDRESS_INCREMENT

    # print(label_addresses)

    # Third pass: Generate machine code
    address = 0
    machine_code = []
    for item in ast.value:
        # Only process instructions now
        if hasattr(item.value, '__iter__'):
            instruction = item.value[0].value
            arguments = [it.value for it in item.value[1:]]
            arguments = list(map(lambda arg: label_addresses[arg] if isinstance(arg, Label) else arg, arguments))
            # print(arguments)
            machine_code.append(instruction.to_machine_code(address, *arguments))
            address += ADDRESS_INCREMENT

    with open(outfile, 'w') as outfile:
        for instruction in machine_code:
            outfile.write('{:04x}\n'.format(instruction))


if __name__ == '__main__':
    main()
