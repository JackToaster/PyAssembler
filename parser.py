from instructions import r_instructions, reduced_r_instructions, i_instructions, j_instructions, nop_instructions, \
    reserved_names
from registers import registers
import re


class ParseResult:
    def __init__(self, loc, value):
        self.loc = loc
        self.value = value

    def error(self):
        return False

    def map(self, fn):
        return ParseResult(self.loc, fn(self.value))

    def __repr__(self):
        return '{}:({})'.format(self.loc, repr(self.value))


class ParseError(ParseResult):
    def __init__(self, loc, error_msg, causes=None):
        super(ParseError, self).__init__(loc, None)
        if causes is None:
            causes = []
        self.error_msg = error_msg
        self.causes = causes

    def error(self):
        return True

    # Do not map error values
    def map(self, fn):
        return self

    def __repr__(self):
        return '{}: Error: {}. Causes: {}'.format(self.loc, self.error_msg, self.causes)


class ParserInput:
    def __init__(self, text, loc=0):
        self.text = text  # The actual text to parse
        self.loc = loc  # Stores where in the text parsing is occuring

    def advance(self, n):
        return ParserInput(self.text, self.loc + n)

    # Remaining text
    def rtext(self):
        if self.loc >= len(self.text):
            return ''
        else:
            return self.text[self.loc:]

    def get_line(self, loc):
        idx = max(0, self.text.rfind('\n', 0, loc))  # Start of line or start of string
        line = re.match('.*$', self.text[idx + 1:], flags=re.MULTILINE).group(0)  # Text up to end of line/string
        line_no = self.text[:idx].count('\n') + 2
        return line, idx, line_no

    def display_error(self, error: ParseError, max_depth, max_breadth, indent=0, parent_index=-1):
        if max_depth <= 0:
            return

        # Print error and line
        indent_str = ' ' * indent
        error_line, error_line_idx, error_line_no = self.get_line(error.loc)
        line_character = error.loc - error_line_idx
        print(indent_str + '({},{}): Expected {}'.format(error_line_no, line_character, error.error_msg))

        # Don't re-print location of error
        if error.loc != parent_index:
            arrow_offset = len(str(error_line_no)) + line_character
            print(indent_str + '{}>>> {}'.format(error_line_no, error_line))
            print(indent_str + '   {}^'.format(' ' * arrow_offset))

        # Print potential causes
        if len(error.causes) > max_breadth:
            print(indent_str + '    Caused by: Expected one of {} possible inputs.'.format(len(error.causes)))
        elif len(error.causes) > 0:
            print(indent_str + '    Caused by:')
            for cause in error.causes:
                self.display_error(cause, max_depth - 1, max_breadth, indent=indent+4, parent_index=error.loc)








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
def parse_whitespace(i: ParserInput) -> (ParseResult, ParserInput):
    text = i.rtext()
    stripped = text.lstrip()
    if len(stripped) == len(text):
        return ParseError(i.loc, 'whitespace'), i
    else:
        return ParseResult(i.loc, Whitespace()), i.advance(len(text) - len(stripped))


# Parse a single-line comment (Starts with ; or #, ends at end of line)
def parse_comment(i: ParserInput) -> (ParseResult, ParserInput):
    comment_characters = re.match('[#;].*$', i.rtext(), flags=re.MULTILINE)
    if comment_characters is None:
        return ParseError(i.loc, 'comment'), i
    else:
        match_text = comment_characters.group(0)
        return ParseResult(i.loc, Comment(match_text)), i.advance(len(match_text))


def parse_label(i: ParserInput) -> (ParseResult, ParserInput):
    label_characters = re.match('[a-zA-Z_][a-zA-Z0-9_]*', i.rtext())
    if label_characters is None:
        return ParseError(i.loc, 'label'), i
    else:
        match_text = label_characters.group(0)
        if match_text in reserved_names:
            return ParseError(i.loc, 'label'), i
        return ParseResult(i.loc, Label(match_text)), i.advance(len(match_text))


# Returns an exact match for the string
def parse_string(s, case_sensitive=False):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        text = i.rtext()
        if case_sensitive:
            if text.startswith(s):
                return ParseResult(i.loc, s), i.advance(len(s))
        else:
            if text.lower().startswith(s.lower()):
                return ParseResult(i.loc, s), i.advance(len(s))
        return ParseError(i.loc, 'string "{}"'.format(s)), i

    return parse_fn


def parser_numeric_literal(i: ParserInput) -> (ParseResult, ParserInput):
    literal_character = re.match('-?[0-9A-Fxb]+', i.rtext())
    if literal_character is None:
        return ParseError(i.loc, 'numeric literal'), i
    else:
        try:
            match_text = literal_character.group(0)
            return ParseResult(i.loc, int(match_text, 0)), i.advance(len(match_text))
        except ValueError:
            return ParseError(i.loc, 'valid numeric literal'), i


# Returns the result of the first parser that succeeds
def parse_any(*parsers, error_msg):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        failure_causes = []
        for parser in parsers:
            output, rem = parser(i)
            if not output.error():
                return output, rem
            else:
                failure_causes.append(output)

        return ParseError(i.loc, error_msg, causes=failure_causes), i

    return parse_fn


# Runs a parser zero or more times and returns a list of the output. Cannot fail.
def zero_or_more_of(parser):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        loc = i.loc
        output = []
        while True:
            parse_output, rem = parser(i)
            if parse_output.error():
                return ParseResult(loc, output), i
            else:
                output.append(parse_output)
                i = rem

    return parse_fn


# Same as above, but fails if none are found
def one_or_more_of(parser):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        loc = i.loc
        output = []

        parse_output, rem = parser(i)
        if parse_output.error():
            return parse_output, rem
        output.append(parse_output)
        i = rem
        while True:
            parse_output, rem = parser(i)
            if parse_output.error():
                return ParseResult(loc, output), i
            else:
                output.append(parse_output)
                i = rem

    return parse_fn


# Runs a parser for all of the output. Fails on any error.
def parse_all(parser):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        loc = i.loc
        output = []
        while i.rtext() != '':
            parse_output, rem = parser(i)
            if parse_output.error():
                return parse_output, i
            else:
                output.append(parse_output)
                i = rem
        return ParseResult(loc, output), i

    return parse_fn


# Always succeeds, returns empty output if parser fails.
def optional(parser):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        output, rem = parser(i)
        if output.error():
            return ParseResult(i.loc, None), i
        else:
            return output, rem

    return parse_fn


# Runs a sequence of parsers, and returns a list of their outputs. Fails if any parser fails.
def sequence(*parsers, custom_error_msg=None):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        loc = i.loc
        output = []
        for parser in parsers:
            parse_output, rem = parser(i)
            if parse_output.error():
                if custom_error_msg is not None:
                    return ParseError(i.loc, custom_error_msg, causes=[parse_output]), i
                else:
                    return parse_output, i
            else:
                output.append(parse_output)
                i = rem
        return ParseResult(loc, output), i

    return parse_fn


# Applies a function to the returned value of a parser if it succeeds
def parser_map(parser, map_fn):
    def parse_fn(i: ParserInput) -> (ParseResult, ParserInput):
        output, rem = parser(i)
        if not output.error():
            return ParseResult(output.loc, map_fn(output.value)), rem
        return output, rem

    return parse_fn


# Returns the output of the left parser out of a given pair
def left(left_parser, right_parser):
    return parser_map(sequence(left_parser, right_parser), lambda output: output[0].value)


# Returns the output of the right parser out of a given pair
def right(left_parser, right_parser):
    return parser_map(sequence(left_parser, right_parser), lambda output: output[1].value)


def wrap_whitespace(parser):
    return left(right(optional_whitespace, parser), optional_whitespace)


def parse_any_string(*strings, error_msg):
    return parse_any(*[parse_string(s) for s in strings], error_msg=error_msg)


def parse_mnemonic(instr_list, error_msg):
    return parser_map(
        parse_any_string(*[inst.name for inst in instr_list], error_msg=error_msg),
        lambda name: get_obj_by_name(instr_list, name)
    )


whitespace_and_comment = one_or_more_of(parse_any(parse_whitespace, parse_comment, error_msg='whitespace or comment'))

optional_whitespace = optional(whitespace_and_comment)

parse_register = parser_map(
    parse_any_string(*[r.name for r in registers], error_msg='register name'),
    lambda name: get_obj_by_name(registers, name)
)

parse_r_type = sequence(
    parse_mnemonic(r_instructions, error_msg='R-type instruction'),  # Instruction mnemonic, e.g. 'addi'
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
    parse_mnemonic(reduced_r_instructions, '2-operand R-type instruction'),  # Instruction mnemonic, e.g. 'addi'
    right(parse_whitespace, parse_register),  # Register rd (must have whitespace beforehand)
    right(  # Ignore return value from comma, keep register
        wrap_whitespace(parse_string(',')),  # Comma separating registers (plus any amount of whitespace)
        parse_register  # Register rs
    )
), lambda out: out + [ParseResult(-1, registers[0])])


def flatten_list(lst):
    outlist = []
    for it in lst:
        val = it.value
        if hasattr(val, '__iter__'):
            outlist = outlist + flatten_list(val)
        else:
            outlist.append(it)
    return outlist


parse_i_type = parser_map(sequence(
    parse_mnemonic(i_instructions, error_msg='I-type instruction'),
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
                    parse_any(parser_numeric_literal, parse_label, error_msg='numeric literal or label')  # immediate/label
                )
            ),
            parser_map(  # Second option (parentheses)
                sequence(
                    parser_numeric_literal,
                    left(right(wrap_whitespace(parse_string('(')), parse_register), wrap_whitespace(parse_string(')')))
                ), lambda output: (output[1], output[0])  # Swap order since literal comes first
            ),
            error_msg='valid i-type arguments'
        )
    )
), lambda out: flatten_list(out))  # since this got hierarchical, un-hierarchy it

# J type is just a mnemonic plus literal/label
parse_j_type = sequence(
    parse_mnemonic(j_instructions, error_msg='J-type instruction'),
    right(parse_whitespace, parse_any(parser_numeric_literal, parse_label, error_msg='numeric literal or label'))
)

parse_nop = sequence(parse_mnemonic(nop_instructions, error_msg='NOP'))

parse_instruction = parse_any(parse_r_type, parse_reduced_r_type, parse_i_type, parse_j_type, parse_nop, error_msg='an instruction')

# Parse a label on a new line, with format "label: ...." or "label ...." (colon is optional)
line_label = left(parse_label, optional(parse_string(':')))

parse_asm = parse_all(wrap_whitespace(parse_any(parse_instruction, line_label, error_msg='an instruction or label')))
