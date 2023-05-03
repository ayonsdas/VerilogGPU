import os
import re
import struct
import sys
import numpy as np
import imageio


# TODO: fix register type varying betwenen registers (array vs [])

# from assembly_preprocessor import AssemblyPreprocessor
from float_binary_converter import float_to_binary
from data import mem

num_registers = 16
register_size = 32
bit_width = 16

registers = [np.zeros(register_size, dtype='float16') for _ in range(num_registers)]

num_shared_registers = 16
shared_registers = np.zeros(num_shared_registers, dtype='uint16')

memory_size = 2**16
memory = np.zeros(memory_size, dtype='uint16')

# read minecraft.png 32x32
minecraft = imageio.v2.imread('minecraft.png')
# extract red channel as array
red = minecraft[:, :, 0]
# convert to 16-bit unsigned integer
red = np.uint16(red)
# convert to 16-bit half-precision floating-point
red = np.float16(red)
# convert from (32, 32) to (1024)
red = red.reshape(1024)
# change from [0, 255] to [0, 1]
red = red / 255
# view as 16-bit unsigned integer
red = np.uint16(red.view('H'))
# write to memory starting at address 30000
memory[32000:32000+32*32] = red
# extract green channel as array
green = minecraft[:, :, 1]
# convert to 16-bit unsigned integer
green = np.uint16(green)
# convert to 16-bit half-precision floating-point
green = np.float16(green)
# convert from (32, 32) to (1024)
green = green.reshape(1024)
# change from [0, 255] to [0, 1]
green = green / 255
# view as 16-bit unsigned integer
green = np.uint16(green.view('H'))
# write to memory starting at address 30000
memory[32000+32*32:32000+32*32*2] = green
# extract blue channel as array
blue = minecraft[:, :, 2]
# convert to 16-bit unsigned integer
blue = np.uint16(blue)
# convert to 16-bit half-precision floating-point
blue = np.float16(blue)
# convert from (32, 32) to (1024)
blue = blue.reshape(1024)
# change from [0, 255] to [0, 1]
blue = blue / 255
# view as 16-bit unsigned integer
blue = np.uint16(blue.view('H'))
# write to memory starting at address 30000
memory[32000+32*32*2:32000+32*32*3] = blue

# print hex of texture data
mem_texture = memory[32000:32000+32*32*3]
# convert to hex
# mem_texture = [hex(x).upper()[2:] for x in mem_texture]
# needed to pad hex with zeros
mem_texture = [hex(x).upper()[2:].zfill(4) for x in mem_texture]

# # print texture data to TEXDUMP.hex
# with open('TEXDUMP.hex', 'w') as f:
#     # write 128 characters per line
#     for i in range(0, len(mem_texture), 128):
#         f.write(''.join(mem_texture[i:i+128]) + '\n')
    

#     # for line in mem_texture:
#     #     f.write(line)
    
#     f.close()

for k, v in mem.items():
    memory[k : k + 32] = [np.uint16(np.float16(v).view('H'))] * 32

num_masks = 64
mask_stack_top = 0 # index of top element of the mask stack
mask_stack = np.zeros((num_masks, register_size), dtype='uint32')
# initialize first mask to all 1s
mask_stack[0] = np.ones(register_size, dtype='uint32')

# # memory [0-255] should be counting from 0 to 255
# for i in range(256):
#     memory[i] = np.uint16(np.float16(i).view('H'))

# memory [50000:] has triangle data
# # vertex x
# memory[32000] = np.uint16(np.float16(32).view('H'))
# memory[32320] = np.uint16(np.float16(64).view('H'))
# memory[32640] = np.uint16(np.float16(128).view('H'))
# # vertex y
# memory[34280] = np.uint16(np.float16(32).view('H'))
# memory[34600] = np.uint16(np.float16(64).view('H'))
# memory[33005] = np.uint16(np.float16(16).view('H'))

output_width = 256
output_height = 256

# Create a 256x256x4 NumPy array with half-precision floating-point numbers
# The 4 channels represent: Red, Green, Blue, and Depth
# output_screen = np.zeros((output_height, output_width, 4), dtype=np.float16)

current_instruction = 0

# x, y = 128, 64
# r, g, b, depth = 0.5, 0.25, 0.75, 0.1
# output_screen[y, x] = (r, g, b, depth)

############################################
# instructions
############################################


# adds s_rt, s_ra, s_rb // s_rt = s_ra + s_rb
def add_shared(s_rt, s_ra, s_rb):
    shared_registers[s_rt] = (shared_registers[s_ra] + shared_registers[s_rb]) % 2**bit_width

# subs s_rt, s_ra, s_rb // s_rt = s_ra - s_rb
def sub_shared(s_rt, s_ra, s_rb):
    shared_registers[s_rt] = (shared_registers[s_ra] - shared_registers[s_rb]) % 2**bit_width

# muls s_rt, s_ra, s_rb // s_rt = s_ra * s_rb
def mul_shared(s_rt, s_ra, s_rb):
    shared_registers[s_rt] = (shared_registers[s_ra] * shared_registers[s_rb]) % 2**bit_width

# divs s_rt, s_ra, s_rb // s_rt = s_ra / s_rb
def div_shared(s_rt, s_ra, s_rb):
    shared_registers[s_rt] = (shared_registers[s_ra] / shared_registers[s_rb]) % 2**bit_width

# add rt, ra, rb // rt = ra + rb
def add_vector(rt, ra, rb):
    """Add two vector registers and store the result in a third vector register, values are already float16"""
    # registers[rt] = [a + b for a, b in zip(registers[ra], registers[rb])]
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [a + b if mask_stack[mask_stack_top][i] else registers[rt][i] for i, (a, b) in enumerate(zip(registers[ra], registers[rb]))]


# sub rt, ra, rb // rt = ra - rb
def sub_vector(rt, ra, rb):
    """Subtract two vector registers and store the result in a third vector register, values are already float16"""
    # registers[rt] = [a - b for a, b in zip(registers[ra], registers[rb])]
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [a - b if mask_stack[mask_stack_top][i] else registers[rt][i] for i, (a, b) in enumerate(zip(registers[ra], registers[rb]))]

# mul rt, ra, rb // rt = ra * rb
def mul_vector(rt, ra, rb):
    # registers[rt] = [a * b for a, b in zip(registers[ra], registers[rb])]
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [a * b if mask_stack[mask_stack_top][i] else registers[rt][i] for i, (a, b) in enumerate(zip(registers[ra], registers[rb]))]

# div rt, ra, rv // rt = ra / rb
def div_vector(rt, ra, rb):
    # registers[rt] = [a / b for a, b in zip(registers[ra], registers[rb])]
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [a / b if mask_stack[mask_stack_top][i] else registers[rt][i] for i, (a, b) in enumerate(zip(registers[ra], registers[rb]))]

# mov rt, imm16 (half-precision floating point) // rt = imm16 for all 32 elements
def mov_vector(rt: int, imm16: np.float16) -> None:
    """Move a 16-bit value into a vector register, half-precision floating-point version."""
    # Store the value in all 32 elements of the target vector register
    # registers[rt] = [imm16] * register_size
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [imm16 if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# movl rt, s_ra // fills all threads of rt with value of lower byte of s_ra converted to float16
def movl_vector(rt, s_ra):
    # """Move the lower byte of a shared register into all elements of a vector register, interpreting as float16."""
    # # Get the lower byte of the value in the source shared register
    # lower_byte = shared_registers[s_ra] & 0xFF
    """Move a shared register mod 2048 into all elements of a vector register."""
    # Get the source shared register value mod 2048
    lower_byte = shared_registers[s_ra] % 2048

    # Convert the lower byte to a half-precision floating-point number
    float16_value = np.float16(lower_byte) # struct.unpack('e', struct.pack('B', lower_byte))[0]

    # Store the value in all 32 elements of the target vector register
    # registers[rt] = [float16_value] * register_size
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [float16_value if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# movidx rt // each thread gets the thread index in rt (as floating point)
def movidx_vector(rt):
    """Move the thread index into all elements of a vector register, as a float16."""
    for i in range(register_size):
        # registers[rt][i] = np.float16(i)
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = np.float16(i) if mask_stack[mask_stack_top][i] else registers[rt][i]

# movraw rt, s_ra (copy raw binary frmo s_ra to rt, no conversion)
def movraw_vector(rt, s_ra):
    """Move the raw binary value of a shared register into all elements of a vector register."""
    # Get the value in the source shared register
    value = shared_registers[s_ra]
    # Convert the value to a half-precision floating-point number, preserving binary representation
    value = np.float16(value.view('H')) # TODO: check that this works
    # Store the value in all 32 elements of the target vector register
    # registers[rt] = [value] * register_size
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [value if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# movs s_rt, imm16 // s_rt = imm16
def mov_shared(s_rt, imm16):
    """Move a 16-bit value into a shared register, 16-bit unsigned integer version."""
    # Store the value in the target shared register
    shared_registers[s_rt] = imm16

# movpart s_rt, ra // moves round(ra[0]) into s_rt
def movpart_shared(s_rt, ra):
    """Move the rounded value of the first element of a vector register into a shared register."""
    # Store the rounded value of the first element of the source vector register in the target shared register
    shared_registers[s_rt] = round(registers[ra][0])

# ld rt, s_ra //load vector at address s_ra to rt (copy paste raw memory)
# ldall rt, s_ra //fills all threads of rt with 16-bit value at address s_ra
# st s_rt, ra // mem[s_rt] (16*32 bits) = ra

# ld rt, s_ra //load vector at address s_ra to rt (copy paste raw memory)
def load_vector(rt, s_ra):
    """Load a vector from memory into a vector register, interpreting as float16."""
    # Get the address of the first element of the vector
    address = shared_registers[s_ra]

    # Load the vector from memory and convert it to half-precision floating point
    uint16_vector = memory[address:address + register_size]
    float16_vector = uint16_vector.view('float16')

    # Store the float16 vector in the target vector register
    # registers[rt] = float16_vector
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [float16_vector[i] if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# ldall rt, s_ra //fills all threads of rt with 16-bit value at address s_ra
def load_all_vector(rt, s_ra):
    """Load a 16-bit value from memory into all elements of a vector register, interpreting as float16."""
    # Get the address of the first element of the vector
    address = shared_registers[s_ra]

    # Load the value from memory and interpret it as a half-precision floating-point number
    uint16_value = memory[address]
        # Convert the binary representation of uint16_value to a 16-bit floating-point value
    float16_value = struct.unpack('e', struct.pack('H', uint16_value))[0]

    # Store the float16 value in all elements of the target vector register
    # registers[rt] = [float16_value] * register_size
    # only do operation for elements where mask is 1, otherwise keep value
    registers[rt] = [float16_value if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# lds s_rt, s_ra //load 2 bytes at address s_ra to s_rt
def load_shared(s_rt, s_ra):
    """Load a 16-bit value from memory into a shared register."""
    # Get the address of the value in memory
    address = shared_registers[s_ra]

    # Load the value from memory
    shared_registers[s_rt] = memory[address]

# ldtex32 rt, ra, rb, s_ra //rt[i] = mem[s_ra+round(ra[i])+32*round(rb[i])]
def load_texture32_vector(rt, ra, rb, s_ra):
    """Load a 32-bit value from memory for each thread of a vector register, interpreting as float16."""
    # Get the addresses of each element of the vector
    addresses = [shared_registers[s_ra] + np.round(registers[ra][i]).astype(int) + 32 * np.round(registers[rb][i]).astype(int) for i in range(register_size)]
    # Load the values from memory and interpret them as half-precision floating-point numbers
    uint16_vector = [memory[address] for address in addresses]
    float16_vector = [struct.unpack('e', struct.pack('H', uint16_value))[0] for uint16_value in uint16_vector]
    # Store the float16 vector in the target vector register
    registers[rt] = [float16_vector[i] if mask_stack[mask_stack_top][i] else registers[rt][i] for i in range(register_size)]

# st s_rt, ra // mem[s_rt] (16*32 bits) = ra
def store_vector(s_rt, ra):
    """Store a vector register into memory, interpreting as uint16."""
    # Get the address of the first element of the vector
    address = shared_registers[s_rt]

    # # Convert the float16 values in the vector register to uint16 values
    # uint16_vector = registers[ra].view('uint16')
    uint16_vector = [np.float16(registers[ra][i]).view('uint16') for i in range(register_size)]

    # Store the uint16 vector in memory
    # memory[address:address + register_size] = uint16_vector
    # only do operation for elements where mask is 1, otherwise keep value
    memory[address:address + register_size] = [uint16_vector[i] if mask_stack[mask_stack_top][i] else memory[address:address + register_size][i] for i in range(register_size)]

# sts s_rt, s_ra // mem[s_rt] (16 bits) = s_ra
def store_shared(s_rt, s_ra):
    """Store a shared register into memory, interpreting as uint16."""
    # Get the address of the first element of the vector
    address = shared_registers[s_rt]

    # Store the uint16 value in memory
    memory[address] = shared_registers[s_ra]

# pushmask // pushes the current mask
# popmask // pops from the mask stack to current mask
# peekmask ra // copies the top of the mask stack to the vector register ra
# andmask ra // ands the current mask with ra (elementwise)
# andmasks s_ra // ands the current mask with s_ra
# invertmask // inverts the current mask
# jmpmask imm16 // jumps if at least 1 bit of the mask
# jmpnotmask imm16 // jumps if no bits of the mask

# pushmask // push current mask to mask stack
def push_mask():
    """Push a mask to the mask stack."""
    global mask_stack_top
    # Push the mask to the stack
    mask_stack_top += 1
    mask_stack[mask_stack_top] = mask_stack[mask_stack_top - 1]

# popmask // pop mask from stack to current mask
def pop_mask():
    """Pop a mask from the mask stack."""
    global mask_stack_top
    # Pop the mask from the stack
    # mask = mask_stack[mask_stack_top]
    mask_stack_top -= 1

# peekmask rt // copies the top of the mask stack to the vector register ra
def peek_mask(rt):
    """Copy the top of the mask stack to a vector register."""
    # Copy the mask from the stack to the target vector register
    registers[rt] = mask_stack[mask_stack_top - 1]

# andmask ra // ands the current mask with ra (elementwise)
def and_mask(ra):
    """And the current mask with a vector register."""
    # # And the current mask with the target vector register
    # mask_stack[mask_stack_top] &= registers[ra]
    # And each bit of the mask with the corresponding thread of the target vector register
    for i in range(register_size):
        reg_bool = registers[ra][i] != 0
        mask_stack[mask_stack_top][i] &= reg_bool

# andmasks s_ra // ands the current mask with s_ra
def and_shared_mask(s_ra):
    """And the current mask with a shared register."""
    # # And the current mask with the target vector register
    # mask_stack[mask_stack_top] &= registers[ra]
    # And each bit of the mask with the corresponding thread of the target vector register
    for i in range(register_size):
        reg_bool = shared_registers[s_ra] != 0
        mask_stack[mask_stack_top][i] &= reg_bool

# invertmask // inverts the current mask
def invert_mask():
    """Invert the current mask."""
    # Invert the current mask
    mask_stack[mask_stack_top] = ~mask_stack[mask_stack_top]

# jmpmask imm16 // jumps if at least 1 bit of the mask
def jump_mask(imm16):
    """Jump if at least one bit of the current mask is set."""
    global current_instruction
    # Jump if at least one bit of the current mask is set
    if mask_stack[mask_stack_top].any():
        return imm16
    else:
        return current_instruction + 1

# jmpnotmask imm16 // jumps if no bits of the mask
def jump_not_mask(imm16):
    """Jump if no bits of the current mask are set."""
    global current_instruction
    # Jump if no bits of the current mask are set
    if not mask_stack[mask_stack_top].any():
        return imm16
    else:
        return current_instruction + 1

# boolean operations vector registers
# and rt, ra, rb [same format for below boolean instructions]
# or rt, ra, rb
# not rt, ra
# gt rt, ra, rb (rt = ra > rb, rt=bool, ra,rb=float)
# lt (rt = ra < rb, rt=bool, ra,rb=float)
# gte rt, ra, rb (rt = ra >= rb, rt=bool, ra,rb=float)
# lte (rt = ra <= rb, rt=bool, ra,rb=float)

# and rt, ra, rb // rt = ra & rb (elementwise)
def and_vector(rt, ra, rb):
    """And two vector registers bitwise per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] & registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] & registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]

# or rt, ra, rb // rt = ra | rb (elementwise)
def or_vector(rt, ra, rb):
    """Or two vector registers bitwise per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] | registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] | registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]

# not rt, ra // rt = ~ra (elementwise)
def not_vector(rt, ra):
    """Not a vector register bitwise per element."""
    for i in range(register_size):
        # registers[rt][i] = ~registers[ra][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = ~registers[ra][i] if mask_stack[mask_stack_top][i] else registers[rt][i]

# gt rt, ra, rb // rt = ra > rb (elementwise)
def gt_vector(rt, ra, rb):
    """Greater than two vector registers per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] > registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] > registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]

# lt rt, ra, rb // rt = ra < rb (elementwise)
def lt_vector(rt, ra, rb):
    """Less than two vector registers per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] < registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] < registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]
        
# gte rt, ra, rb // rt = ra >= rb (elementwise)
def gte_vector(rt, ra, rb):
    """Greater than or equal to two vector registers per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] >= registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] >= registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]

# lte rt, ra, rb // rt = ra <= rb (elementwise)
def lte_vector(rt, ra, rb):
    """Less than or equal to two vector registers per element."""
    for i in range(register_size):
        # registers[rt][i] = registers[ra][i] <= registers[rb][i]
        # only do operation for elements where mask is 1, otherwise keep value
        registers[rt][i] = registers[ra][i] <= registers[rb][i] if mask_stack[mask_stack_top][i] else registers[rt][i]




# boolean operations shared
# ands s_rt, s_ra, s_rb
# ors s_rt, s_ra, s_rb
# nots s_rt, s_ra
# gts (s_rt = s_ra > s_rb, s_rt=bool, s_ra,s_rb=int)
# lts (s_rt = s_ra < s_rb, s_rt=bool, s_ra,s_rb=int)
# gtes (s_rt = s_ra >= s_rb, s_rt=bool, s_ra,s_rb=int)
# ltes (s_rt = s_ra <= s_rb, s_rt=bool, s_ra,s_rb=int)

# ands s_rt, s_ra, s_rb // s_rt = s_ra & s_rb
def and_shared_bitwise(s_rt, s_ra, s_rb):
    """Bitwise and two shared registers."""
    # Bitwise and the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] & shared_registers[s_rb]

# ors s_rt, s_ra, s_rb // s_rt = s_ra | s_rb
def or_shared_bitwise(s_rt, s_ra, s_rb):
    """Bitwise or two shared registers."""
    # Bitwise or the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] | shared_registers[s_rb]

# nots s_rt, s_ra // s_rt = ~s_ra
def not_shared_bitwise(s_rt, s_ra):
    """Bitwise not a shared register."""
    # Bitwise not the shared register
    shared_registers[s_rt] = ~shared_registers[s_ra]

# gts (s_rt = s_ra > s_rb, s_rt=bool, s_ra,s_rb=int)
def gt_shared(s_rt, s_ra, s_rb):
    """Compare two shared registers."""
    # Compare the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] > shared_registers[s_rb]

# lts (s_rt = s_ra < s_rb, s_rt=bool, s_ra,s_rb=int)
def lt_shared(s_rt, s_ra, s_rb):
    """Compare two shared registers."""
    # Compare the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] < shared_registers[s_rb]

# gtes (s_rt = s_ra >= s_rb, s_rt=bool, s_ra,s_rb=int)
def gte_shared(s_rt, s_ra, s_rb):
    """Compare two shared registers."""
    # Compare the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] >= shared_registers[s_rb]

# ltes (s_rt = s_ra <= s_rb, s_rt=bool, s_ra,s_rb=int)
def lte_shared(s_rt, s_ra, s_rb):
    """Compare two shared registers."""
    # Compare the two shared registers
    shared_registers[s_rt] = shared_registers[s_ra] <= shared_registers[s_rb]


# wrscreen // no parameters, writes 32 pixels in a row to the screen with red=r0, green=r1, blue=r2, depth=r3, x=s_r0, y=s_r1
def writeVectorPixels():
    # Get x and y coordinates from the shared registers
    x = shared_registers[0]
    y = shared_registers[1]

    r = registers[0]
    g = registers[1]
    b = registers[2]
    depth = registers[3]

    # note: no newlines in print statements
    # print red as binary text
    for i in range(register_size)[::-1]:
        # temp = float_to_binary(r[i])
        print(float_to_binary(r[i]), end='')
    # print green as binary text
    for i in range(register_size)[::-1]:
        print(float_to_binary(g[i]), end='')
    # print blue as binary text
    for i in range(register_size)[::-1]:
        print(float_to_binary(b[i]), end='')
    # print depth as binary text
    for i in range(register_size)[::-1]:
        print(float_to_binary(depth[i]), end='')
    # print mask as binary text
    for i in range(register_size): # [::-1]:
        # print(bin(mask_stack[mask_stack_top][i])[2:], end='')
        print(format(mask_stack[mask_stack_top][i], '01b'), end='')
    # print x as binary text 16 bits
    print(format(x, '016b'), end='')
    # print y as binary text
    print(format(y, '016b'), end='')
    

    # # Write the pixel data to the output screen
    # for i, (r, g, b, depth) in enumerate(zip(registers[0], registers[1], registers[2], registers[3])):
    #     pixel_x = (x + i)
    #     pixel_y = y
    #     if mask_stack[mask_stack_top][i] == 0:
    #         continue
    #     if pixel_x >= 0 and pixel_y >= 0 and pixel_x < output_width and pixel_y < output_height: # and depth > output_screen[pixel_y, pixel_x, 3]:
    #         # write the pixel
    #         # output_screen[pixel_y, pixel_x] = (r, g, b, depth)

    #         # print binary of pixel
    #         r = np.float16(0.5)
    #         g = np.float16(0.25)
    #         b = np.float16(0.75)
    #         depth = np.float16(1.0)

    #         r_bin = bin(int(r.hex(), 16))[2:].zfill(16)
    #         g_bin = bin(int(g.hex(), 16))[2:].zfill(16)
    #         b_bin = bin(int(b.hex(), 16))[2:].zfill(16)
    #         depth_bin = bin(int(depth.hex(), 16))[2:].zfill(16)

    #         print(f'{r_bin} {g_bin} {b_bin} {depth_bin}')



############################################
# helper functions
############################################

def get_half(value):
    """Convert a python integer [0, 255] to a half-precision floating-point number [0, 1]"""
    # Ensure the input value is within the valid range
    value = np.clip(value, 0, 255)

    # Convert the value to a float in the range [0, 1]
    float_value = value / 255.0

    # Cast the float value to a numpy float16
    half_value = np.float16(float_value)

    return half_value


############################################
# temporary running instructions
############################################

# with open('yeehaw.gpuasm', 'r') as f:
#     lines = f.readlines()
# lines = sys.stdin.readlines()
if len(sys.argv) >= 2:
    filename = sys.argv[1]
else:
    filename = 'intermediate.gpuasm'
    pass

# filename = "intermediate.gpuasm" # sys.argv[1] + "

with open(filename, 'r') as f:
    instructions = f.readlines()

# print(instructions)
# preprocessor = AssemblyPreprocessor()
# instructions = preprocessor.preprocess(instructions)
# # delete intermediate.gpuasm
# os.remove('intermediate.gpuasm')


# for line in lines:
#     line = line.strip()
#     if not line:
#         continue
#     if "//" in line:
#         line = line[:line.index("//")].strip()
#     if "#" in line:
#         line = line[:line.index("#")].strip()
#     if ";" in line:
#         line = line[:line.index(";")].strip()
#     if len(line) > 0:
#         instructions.append(line)

def shared_reg_num(reg_name):
    if reg_name[0:3] == 's_r':
        return int(reg_name[3:])
    else:
        # print('ERROR: invalid shared register name:', reg_name)
        # throw excpetion instead of printing
        raise Exception('ERROR: invalid shared register name:', reg_name)

def reg_num(reg_name):
    if reg_name[0:1] == 'r':
        return int(reg_name[1:])
    else:
        # print('ERROR: invalid register name:', reg_name)
        # throw excpetion instead of printing
        raise Exception('ERROR: invalid register name:', reg_name)

# adds s_rt, s_ra, s_rb // s_rt = s_ra + s_rb (uint16)
# subs s_rt, s_ra, s_rb // s_rt = s_ra - s_rb (uint16)
# muls s_rt, s_ra, s_rb // s_rt = s_ra * s_rb (uint16)
# divs s_rt, s_ra, s_rb // s_rt = s_ra / s_rb (uint16)
# add rt, ra, rb // rt = ra + rb
# sub rt, ra, rb // rt = ra - rb
# mul rt, ra, rb // rt = ra * rb
# div rt, ra, rv // rt = ra / rb


# mov rt, imm16 (half-precision floating point) // rt = imm16 for all 32 elements
# movs s_rt, imm16 // s_rt = imm16
# movl rt, s_ra // fills all threads of rt with value s_ra mod 2048 converted to float16
# ld rt, s_ra //load vector at address s_ra to rt (copy paste raw memory)
# ldall rt, s_ra //fills all threads of rt with 16-bit value at address s_ra
# st s_rt, ra // mem[s_rt] (16*32 bits) = ra
# sts s_rt, s_ra //mem[s_rt] (16 bits) = s_ra

# pushmask // pushes the current mask
# popmask // pops from the mask stack to current mask
# peekmask rt // copies the top of the mask stack to the vector register ra
# andmask ra // ands the current mask with ra (elementwise)
# andmasks s_ra // ands the current mask with s_ra
# invertmask // inverts the current mask
# jmpmask imm16 // jumps if at least 1 bit of the mask
# jmpnotmask imm16 // jumps if no bits of the mask

# boolean operations vector registers
# and rt, ra, rb [same format for below boolean instructions]
# or rt, ra, rb
# not rt, ra
# gt rt, ra, rb (rt = ra > rb, rt=bool, ra,rb=float)
# lt (rt = ra < rb, rt=bool, ra,rb=float)
# gte rt, ra, rb (rt = ra >= rb, rt=bool, ra,rb=float)
# lte (rt = ra <= rb, rt=bool, ra,rb=float)

# boolean operations shared registers
# ands s_rt, s_ra, s_rb
# ors s_rt, s_ra, s_rb
# nots s_rt, s_ra
# gts (s_rt = s_ra > s_rb, s_rt=bool, s_ra,s_rb=int)
# lts (s_rt = s_ra < s_rb, s_rt=bool, s_ra,s_rb=int)
# gtes (s_rt = s_ra >= s_rb, s_rt=bool, s_ra,s_rb=int)
# ltes (s_rt = s_ra <= s_rb, s_rt=bool, s_ra,s_rb=int)



# wrscreen // no parameters, writes 32 pixels in a row to the screen with red=r0, green=r1, blue=r2, depth=r3, x=s_r0, y=s_r1


# print(len(instructions))

# print("-------------------------")
# print(instructions)
try: 
    while current_instruction < len(instructions):
        # switch on instruction type
        instruction = instructions[current_instruction]
        # parts = re.split('[,\s]+', instruction)
        parts = [part for part in re.split('[,\s]+', instruction) if part]
        # print(current_instruction instruction)
        # print(str(current_instruction) + ": " + instruction)
        instruction_type = parts[0]
        if instruction_type == 'adds':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            add_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'subs':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            sub_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'muls':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            mul_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'divs':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            div_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'add':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            add_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'sub':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            sub_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'mul':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            mul_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'div':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            div_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'mov':
            rt, imm16 = parts[1:]
            rt = reg_num(rt)
            imm16 = np.float16(imm16)
            mov_vector(rt, imm16)
            current_instruction += 1
        elif instruction_type == 'movl':
            rt, s_ra = parts[1:]
            rt = reg_num(rt)
            s_ra = shared_reg_num(s_ra)
            movl_vector(rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'movidx':
            rt = reg_num(parts[1])
            movidx_vector(rt)
            current_instruction += 1
        elif instruction_type == 'movraw':
            rt, s_ra = parts[1:]
            rt = reg_num(rt)
            s_ra = shared_reg_num(s_ra)
            movraw_vector(rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'movs':
            s_rt, imm16 = parts[1:]
            s_rt = shared_reg_num(s_rt)
            imm16 = np.uint16(imm16)
            mov_shared(s_rt, imm16)
            current_instruction += 1
        elif instruction_type == 'movpart':
            s_rt, ra = parts[1:]
            s_rt = shared_reg_num(s_rt)
            ra = reg_num(ra)
            movpart_shared(s_rt, ra)
            current_instruction += 1
        elif instruction_type == 'ld':
            rt, s_ra = parts[1:]
            rt = reg_num(rt)
            s_ra = shared_reg_num(s_ra)
            load_vector(rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'ldall':
            rt, s_ra = parts[1:]
            rt = reg_num(rt)
            s_ra = shared_reg_num(s_ra)
            load_all_vector(rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'lds':
            s_rt, s_ra = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            load_shared(s_rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'ldtex32':
            rt, ra, rb, s_ra = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            s_ra = shared_reg_num(s_ra)
            load_texture32_vector(rt, ra, rb, s_ra)
            current_instruction += 1
        elif instruction_type == 'st':
            s_rt, ra = parts[1:]
            s_rt = shared_reg_num(s_rt)
            ra = reg_num(ra)
            store_vector(s_rt, ra)
            current_instruction += 1
        elif instruction_type == 'sts':
            s_rt, ra = parts[1:]
            s_rt = shared_reg_num(s_rt)
            ra = reg_num(ra)
            store_shared(s_rt, ra)
            current_instruction += 1
        elif instruction_type == 'pushmask':
            push_mask()
            current_instruction += 1
        elif instruction_type == 'popmask':
            pop_mask()
            current_instruction += 1
        elif instruction_type == 'peekmask':
            rt = reg_num(parts[1])
            peek_mask(rt)
            current_instruction += 1
        elif instruction_type == 'andmask':
            ra = reg_num(parts[1])
            and_mask(ra)
            current_instruction += 1
        elif instruction_type == 'andmasks':
            s_ra = shared_reg_num(parts[1])
            and_shared_mask(s_ra)
            current_instruction += 1
        elif instruction_type == 'invertmask':
            invert_mask()
            current_instruction += 1
        elif instruction_type == 'jmpmask':
            imm16 = np.uint16(parts[1])
            current_instruction = jump_mask(imm16)
        elif instruction_type == 'jmpnotmask':
            imm16 = np.uint16(parts[1])
            current_instruction = jump_not_mask(imm16)
        elif instruction_type == 'and':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            and_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'or':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            or_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'not':
            rt, ra = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            not_vector(rt, ra)
            current_instruction += 1
        elif instruction_type == 'gt':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            gt_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'lt':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            lt_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'gte':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            gte_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'lte':
            rt, ra, rb = parts[1:]
            rt = reg_num(rt)
            ra = reg_num(ra)
            rb = reg_num(rb)
            lte_vector(rt, ra, rb)
            current_instruction += 1
        elif instruction_type == 'ands':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            and_shared_bitwise(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'ors':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            or_shared_bitwise(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'nots':
            s_rt, s_ra = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            not_shared_bitwise(s_rt, s_ra)
            current_instruction += 1
        elif instruction_type == 'gts':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            gt_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'lts':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            lt_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'gtes':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            gte_shared(s_rt, s_ra, s_rb)
            current_instruction += 1
        elif instruction_type == 'ltes':
            s_rt, s_ra, s_rb = parts[1:]
            s_rt = shared_reg_num(s_rt)
            s_ra = shared_reg_num(s_ra)
            s_rb = shared_reg_num(s_rb)
            lte_shared(s_rt, s_ra, s_rb)
            current_instruction += 1


        elif instruction_type == 'wrscreen':
            writeVectorPixels()
            current_instruction += 1
        
        elif instruction_type == 'publish':
            print('publish', end='')
            current_instruction += 1
            
        else:
            print('Unknown instruction: {}'.format(instruction_type))
            current_instruction += 1
except Exception as e:
    print(instructions[current_instruction])
    print(parts)
    raise e

# # fill screen with gradient where x is red and y is green. Rows are done 32 at a time
# for i in range(256):

#     for j in range(0, 256, 32):
#         # handle green

#         # mem[0-255] contains lookup table
#         # get start index = j
#         mov_shared(0, j)
#         # fill with thread indexes
#         load_vector(4, 0)

#         # divide r4 by 256
#         mov_vector(5, np.float16(256))
#         div_vector(0, 4, 5)

#         mov_vector(1, get_half(i))
#         # mov_vector_register(1, get_half(255 - i))
#         mov_vector(2, get_half(0))
#         mov_vector(3, get_half(1))
#         mov_shared(0, j)
#         mov_shared(1, i)
#         writeVectorPixels()


############################################
# output
############################################

# def save_output_screen(output_screen, filename):
#     # Clamp the half-precision RGB values to the valid range [0, 1]
#     clamped_output_screen = np.clip(output_screen[:, :, :3], 0, 1)

#     # Convert the clamped half-precision RGB values to 8-bit integers
#     output_rgb = np.uint8(clamped_output_screen * 255)

#     # Save the image as a PNG file
#     imageio.imwrite(filename, output_rgb)


# # Save the output screen as a PNG file
# save_output_screen(output_screen, 'output.png')
