from instructions import r_instructions, reduced_r_instructions, i_instructions, j_instructions, nop_instructions
from registers import registers
import re

COMMENT_CHARACTER = ';'


# Element that returns its name when converted to a string, used for debugging
class Element:
    def __repr__(self):
        return self.__class__.__name__


class Whitespace(Element):
    pass


class Label:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Label({})'.format(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return self.name.__hash__()


class Comment:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Comment({})'.format(self.text)


# Find an object in a list by its 'name' attribute
def get_obj_by_name(lst, name):
    return list(filter(lambda it: it.name == name, lst))[0]


# Parse any amount of whitespace and return a Whitespace object
def parse_whitespace(text):
    parsed = text.lstrip()
    if len(parsed) == len(text):
        return None, text
    else:
        return Whitespace(), parsed


# Parse a single-line comment (Starts with ; or #, ends at end of line)
def parse_comment(text):
    comment_characters = re.match('[#;].*\n', text)
    if comment_characters is None:
        return None, text
    else:
        match_text = comment_characters.group(0)
        return Comment(match_text), text[len(match_text):]


def parse_label(text):
    label_characters = re.match('[a-zA-Z_][a-zA-Z0-9_]*', text)
    if label_characters is None:
        return None, text
    else:
        match_text = label_characters.group(0)
        return Label(match_text), text[len(match_text):]


# Returns an exact match for the string
def parse_string(s, case_sensitive=False):
    def parse_fn(text):
        if case_sensitive:
            if text.startswith(s):
                return s, text[len(s):]
        else:
            if text.lower().startswith(s.lower()):
                return s, text[len(s):]
        return None, text

    return parse_fn


def parser_numeric_literal(text):
    literal_character = re.match('-?[0-9A-Fxb]+', text)
    if literal_character is None:
        return None, text
    else:
        try:
            match_text = literal_character.group(0)
            return int(match_text, 0), text[len(match_text):]
        except ValueError:
            return None, text


# Returns the result of the first parser that succeeds
def parse_any(*parsers):
    def parse_fn(text):
        for parser in parsers:
            output, rem = parser(text)
            if output is not None:
                return output, rem
        return None, text

    return parse_fn


# Runs a parser zero or more times and returns a list of the output. Cannot fail.
def zero_or_more_of(parser):
    def parse_fn(text):
        output = []
        while True:
            parse_output, rem = parser(text)
            if parse_output is None:
                return output, text
            else:
                output.append(parse_output)
                text = rem

    return parse_fn


def one_or_more_of(parser):
    def parse_fn(text):
        output = []

        parse_output, rem = parser(text)
        if parse_output is None:
            return parse_output, rem
        output.append(parse_output)
        text = rem
        while True:
            parse_output, rem = parser(text)
            if parse_output is None:
                return output, text
            else:
                output.append(parse_output)
                text = rem

    return parse_fn


# Always succeeds, returns empty output if parser fails.
def optional(parser):
    def parse_fn(text):
        output, rem = parser(text)
        if output is None:
            return [], text
        else:
            return output, rem

    return parse_fn


# Runs a sequence of parsers, and returns a list of their outputs. Fails if any parser fails.
def sequence(*parsers):
    def parse_fn(text):
        output = []
        for parser in parsers:
            parse_output, rem = parser(text)
            if parse_output is None:
                return None, text
            else:
                output.append(parse_output)
                text = rem
        return output, text

    return parse_fn


def parser_map(parser, map_fn):
    def parse_fn(text):
        output, rem = parser(text)
        if output is not None:
            return map_fn(output), rem
        return output, rem

    return parse_fn


# Returns the output of the left parser out of a given pair
def left(left_parser, right_parser):
    return parser_map(sequence(left_parser, right_parser), lambda output: output[0])


# Returns the output of the right parser out of a given pair
def right(left_parser, right_parser):
    return parser_map(sequence(left_parser, right_parser), lambda output: output[1])


def wrap_whitespace(parser):
    return left(right(optional_whitespace, parser), optional_whitespace)


def parse_any_string(*strings):
    return parse_any(*[parse_string(s) for s in strings])


def parse_mnemonic(instr_list):
    return parser_map(
        parse_any_string(*[inst.name for inst in instr_list]),
        lambda name: get_obj_by_name(instr_list, name)
    )


whitespace_and_comment = one_or_more_of(parse_any(parse_whitespace, parse_comment))

optional_whitespace = optional(whitespace_and_comment)

parse_register = parser_map(
    parse_any_string(*[r.name for r in registers]),
    lambda name: get_obj_by_name(registers, name)
)

parse_r_type = sequence(
    parse_mnemonic(r_instructions),  # Instruction mnemonic, e.g. 'addi'
    right(parse_whitespace, parse_register),  # Register rd (must have whitespace beforehand)
    right(  # Ignore return value from comma, keep register
        wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)
        parse_register  # Register rs
    ),
    right(  # Ignore return value from comma, keep register
        wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)
        parse_register  # Register rt
    ), )

# Parse an R-type instruction that only uses two arguments (E.G. shift by one instructions).
# The third argument is given as zero.
parse_reduced_r_type = parser_map(sequence(
    parse_mnemonic(reduced_r_instructions),  # Instruction mnemonic, e.g. 'addi'
    right(parse_whitespace, parse_register),  # Register rd (must have whitespace beforehand)
    right(  # Ignore return value from comma, keep register
        wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)
        parse_register  # Register rs
    )
), lambda out: out + [registers[0]])


def flatten_list(lst):
    outlist = []
    for it in lst:
        if hasattr(it, '__iter__'):
            outlist = outlist + flatten_list(it)
        else:
            outlist.append(it)
    return outlist


parse_i_type = parser_map(sequence(
    parse_mnemonic(i_instructions),
    right(parse_whitespace, parse_register),  # First register (must have whitespace beforehand)
    right(  # Ignore return value from comma, keep register
        wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)

        # Two different options for i-type syntax:
        # addi $s1, $s2, imm
        # sw $s1, 0($s2)
        parse_any(
            sequence(  # first option
                parse_register,
                right(  # Ignore return value from comma, keep value
                    wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)
                    parse_any(parser_numeric_literal, parse_label)  # immediate/label
                )
            ),
            parser_map(  # Second option (parentheses)
                sequence(
                    parser_numeric_literal,
                    left(right(wrap_whitespace(parse_string('(')), parse_register), wrap_whitespace(parse_string(')')))
                ), lambda output: (output[1], output[0])  # Swap order since literal comes first
            )
        )
    )
), lambda out: flatten_list(out))  # since this got hierarchical, un-hierarchy it

# J type is just a mnemonic plus literal/label
parse_j_type = sequence(
    parse_mnemonic(j_instructions),
    right(parse_whitespace, parse_any(parser_numeric_literal, parse_label))
)

parse_nop = parser_map(
    parse_mnemonic(nop_instructions),
    lambda output: [output]
)

parse_instruction = parse_any(parse_r_type, parse_reduced_r_type, parse_i_type, parse_j_type, parse_nop)

# Parse a label on a new line, with format "label: ...." or "label ...." (colon is optional)
line_label = left(parse_label, optional(parse_string(':')))

parse_asm = zero_or_more_of(wrap_whitespace(parse_any(parse_instruction, line_label)))
