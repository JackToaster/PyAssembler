from instructions import ADDRESS_INCREMENT
from parser import parse_asm, Label, ParserInput

import argparse
from pathlib import Path
import sys

OUTPUT_FORMATS = ['words', 'bytes', 'binary']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', metavar='INPUT', type=str, help='Assembly file to read')
    parser.add_argument('-f', metavar='Format', type=str, default='bytes', help='Format to use when writing output '
                                                                                'file ("words", "bytes", or "binary")')
    parser.add_argument('-o', metavar='OUTPUT', type=str, help='File to write hexadecimal machine code into')

    parser.add_argument('-s', '--skip_odd', action='store_const', const=True, default=False, help='Write zeros to odd addresses')

    args = parser.parse_args()

    asmfile = args.infile
    outfile = args.o

    out_format = args.f.lower()

    # Make sure the output format is one of the implemented formats
    if out_format not in OUTPUT_FORMATS:
        print('Unsupported output format "{}"'.format(out_format))
        sys.exit(1)

    if outfile is None:
        suffix = '.txt' if out_format == 'binary' else '.hex'
        outfile = Path(asmfile)
        outfile = outfile.with_suffix(suffix)

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
            try:
                arguments = list(map(lambda arg: label_addresses[arg] if isinstance(arg, Label) else arg, arguments))
            except KeyError as e:
                missing_label = e.args[0].name
                print('Error: Label "{}" is never defined'.format(missing_label))
                sys.exit(1)
            # print(arguments)
            machine_code.append(instruction.to_machine_code(address, *arguments))
            address += ADDRESS_INCREMENT

    # Write output to file
    with open(outfile, 'w') as outfile:
        if out_format == 'bytes':
            # Header required for Digital to recognize hex file
            outfile.write('v2.0 raw\n')
            for instruction in machine_code:
                word = '{:04x}'.format(instruction)
                # Handle skip odd addresses argument
                if args.skip_odd:
                    # Write individual bytes on separate lines with zero bytes in between
                    outfile.write('{}\n00\n{}\n00\n'.format(word[0:2], word[2:4]))
                else:
                    # Write individual bytes on separate lines
                    outfile.write('{}\n{}\n'.format(word[0:2], word[2:4]))
        elif out_format == 'words':
            # Header required for Digital to recognize hex file
            outfile.write('v2.0 raw\n')
            for instruction in machine_code:
                word = '{:04x}'.format(instruction)

                # Handle skip odd addresses argument
                if args.skip_odd:
                    # Write each 2-byte word on its own line with zeros in between
                    outfile.write('{}\n0000\n'.format(word))
                else:
                    # Write each 2-byte word on its own line
                    outfile.write('{}\n'.format(word))
        elif out_format == 'binary':
            for instruction in machine_code:
                # Write each 2-byte word on its own line in binary
                word = '{:016b}'.format(instruction)
                outfile.write('{}\n'.format(word))

                if args.skip_odd:
                    # write a line of zeros on odd addresses
                    outfile.write('{:016b}\n'.format(0))





if __name__ == '__main__':
    main()
