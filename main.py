from instructions import ADDRESS_INCREMENT
from parser import parse_asm, Label

ASM_FILENAME = 'input.asm'
OUT_FILENAME = 'output.txt'



def main():
    # First pass: Parse text into syntax tree (not a very impressive tree as assembly has no nesting structure)
    with open(ASM_FILENAME, 'r') as asmfile:
        asm_text = asmfile.read()
        ast, rem = parse_asm(asm_text)
        if len(rem) > 0:
            print('Failed to parse file. Remainder: ', rem)  # TODO Make a better error message

    print(ast)

    # Second pass: determine addresses addresses for labels
    address = 0
    label_addresses = {}
    for item in ast:
        if isinstance(item, Label):  # found label, assign value for the following instruction
            if item not in label_addresses.keys():
                label_addresses[item] = address
            else:
                raise SyntaxError('Duplicate label {}'.format(item.name))
        elif hasattr(item, '__iter__'):  # Found instruction, increment address
            address += ADDRESS_INCREMENT

    print(label_addresses)

    # Third pass: Generate machine code
    address = 0
    machine_code = []
    for item in ast:
        # Only process instructions now
        if hasattr(item, '__iter__'):
            instruction = item[0]
            arguments = item[1:]
            arguments = list(map(lambda arg: label_addresses[arg] if isinstance(arg, Label) else arg, arguments))
            print(arguments)
            machine_code.append(instruction.to_machine_code(address, *arguments))
            address += ADDRESS_INCREMENT

    with open(OUT_FILENAME, 'w') as outfile:
        for instruction in machine_code:
            outfile.write('{:04x}\n'.format(instruction))


if __name__ == '__main__':
    main()
