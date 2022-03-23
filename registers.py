
class Register:
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __repr__(self):
        return self.name


# Define registers here.
# Format: Register('$name', register address)
registers = [
    Register('$zero', 0),
    Register('$s0', 1),
    Register('$s1', 2),
    Register('$s2', 3),
    Register('$s3', 4),
    Register('$s4', 5),
    Register('$s5', 6),
    Register('$s6', 7),
]
