# Assembly              Binary machine code     Hex machine code
# R-type instructions
start: add     $s2, $s0, $s1        ;000 001 010 011 0000    0x0530
# I-type instructions
addi    $s0, $zero, -1              ;001 000 001 1111111     0x20FF
bne     $s0, $zero, jump1           ;010 000 001 0000001     0x4081
nop         ;(unused)                0000000000000000        0x0000
jump1: blt     $s0, $zero, jump2    ;011 000 001 0000001     0x6081
nop         ;(unused)                0000000000000000        0x0000
jump2: sw      $s0, 1($zero)        ;101 000 001 0000001     0xA081
lw      $s1, 1 ($zero)               ;100 000 010 0000001     0x8101
# J-type instruction
j    start                          ;110 0000000000000       0xC000


; Assembly              ;Binary machine code     Hex machine code
add $s2, $s0, $s1       ;000 001 010 011 0000    0x0530
asl1 $s2, $s2           ;000 011 000 011 0100    0x0C34
asl1 $s2, $s2           ;000 011 000 011 0100    0x0C34