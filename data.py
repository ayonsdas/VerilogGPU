import numpy as np

# 3x3 rotation matrix around x axis
angle = 0 # -np.pi / 4
cos = np.cos(angle)
sin = np.sin(angle)
rotation_matrix_x = np.array([
    [1, 0, 0],
    [0, cos, -sin],
    [0, sin, cos]
])

# 3x3 rotation matrix around z axis
angle = np.pi / 4
cos = np.cos(angle)
sin = np.sin(angle)
rotation_matrix_z = np.array([
    [cos, -sin, 0],
    [sin, cos, 0],
    [0, 0, 1]
])

# 3x3 rotation matrix around y axis
angle = (np.pi / 2) / 60
cos = np.cos(angle)
sin = np.sin(angle)
rotation_matrix = np.array([
    [cos, 0, sin],
    [0, 1, 0],
    [-sin, 0, cos]
])

# rotation matrix around y axis but axis rotated around x by 30 degrees
# rotation_matrix = np.dot(np.linalg.inv(rotation_matrix_x), np.dot(rotation_matrix, rotation_matrix_x))
rotation_matrix = rotation_matrix_x @ rotation_matrix @ np.linalg.inv(rotation_matrix_x)
# rotation_matrix = np.identity(3)

uv_min = -0.25
uv_max = 15.25

uv_min2 = -0.25 + 16
uv_max2 = 15.25 + 16

tris = [
    # front
    # triangle 1
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : 64,
        'x2' : 64,
        'y2' : -64,
        'z2' : 64,
        'x3' : -64,
        'y3' : 64,
        'z3' : 64,
        'nx1' : 0,
        'ny1' : 0,
        'nz1' : 1,
        'nx2' : 0,
        'ny2' : 0,
        'nz2' : 1,
        'nx3' : 0,
        'ny3' : 0,
        'nz3' : 1,
        'u1' : uv_min,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_min,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # triangle 2
    {
        'x1' : 64,
        'y1' : -64,
        'z1' : 64,
        'x2' : 64,
        'y2' : 64,
        'z2' : 64,
        'x3' : -64,
        'y3' : 64,
        'z3' : 64,
        'nx1' : 0,
        'ny1' : 0,
        'nz1' : 1,
        'nx2' : 0,
        'ny2' : 0,
        'nz2' : 1,
        'nx3' : 0,
        'ny3' : 0,
        'nz3' : 1,
        'u1' : uv_max,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # left
    # triangle 3
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : -64,
        'x2' : -64,
        'y2' : -64,
        'z2' : 64,
        'x3' : -64,
        'y3' : 64,
        'z3' : -64,
        'nx1' : 1,
        'ny1' : 0,
        'nz1' : 0,
        'nx2' : 1,
        'ny2' : 0,
        'nz2' : 0,
        'nx3' : 1,
        'ny3' : 0,
        'nz3' : 0,
        'u1' : uv_min,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_min,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # triangle 4
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : 64,
        'x2' : -64,
        'y2' : 64,
        'z2' : 64,
        'x3' : -64,
        'y3' : 64,
        'z3' : -64,
        'nx1' : 1,
        'ny1' : 0,
        'nz1' : 0,
        'nx2' : 1,
        'ny2' : 0,
        'nz2' : 0,
        'nx3' : 1,
        'ny3' : 0,
        'nz3' : 0,
        'u1' : uv_max,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # back
    # triangle 5
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : -64,
        'x2' : -64,
        'y2' : 64,
        'z2' : -64,
        'x3' : 64,
        'y3' : -64,
        'z3' : -64,
        'nx1' : 0,
        'ny1' : 0,
        'nz1' : -1,
        'nx2' : 0,
        'ny2' : 0,
        'nz2' : -1,
        'nx3' : 0,
        'ny3' : 0,
        'nz3' : -1,
        'u1' : uv_max,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_min,
    },
    # triangle 6
    {
        'x1' : 64,
        'y1' : -64,
        'z1' : -64,
        'x2' : -64,
        'y2' : 64,
        'z2' : -64,
        'x3' : 64,
        'y3' : 64,
        'z3' : -64,
        'nx1' : 0,
        'ny1' : 0,
        'nz1' : -1,
        'nx2' : 0,
        'ny2' : 0,
        'nz2' : -1,
        'nx3' : 0,
        'ny3' : 0,
        'nz3' : -1,
        'u1' : uv_min,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # right
    # triangle 7
    {
        'x1' : 64,
        'y1' : -64,
        'z1' : -64,
        'x2' : 64,
        'y2' : 64,
        'z2' : -64,
        'x3' : 64,
        'y3' : -64,
        'z3' : 64,
        'nx1' : -1,
        'ny1' : 0,
        'nz1' : 0,
        'nx2' : -1,
        'ny2' : 0,
        'nz2' : 0,
        'nx3' : -1,
        'ny3' : 0,
        'nz3' : 0,
        'u1' : uv_max,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_min,
    },
    # triangle 8
    {
        'x1' : 64,
        'y1' : -64,
        'z1' : 64,
        'x2' : 64,
        'y2' : 64,
        'z2' : -64,
        'x3' : 64,
        'y3' : 64,
        'z3' : 64,
        'nx1' : -1,
        'ny1' : 0,
        'nz1' : 0,
        'nx2' : -1,
        'ny2' : 0,
        'nz2' : 0,
        'nx3' : -1,
        'ny3' : 0,
        'nz3' : 0,
        'u1' : uv_min,
        'v1' : uv_min,
        'u2' : uv_max,
        'v2' : uv_max,
        'u3' : uv_min,
        'v3' : uv_max,
    },
    # top
    # triangle 9
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : -64,
        'x2' : 64,
        'y2' : -64,
        'z2' : -64,
        'x3' : -64,
        'y3' : -64,
        'z3' : 64,
        'nx1' : 0,
        'ny1' : 1,
        'nz1' : 0,
        'nx2' : 0,
        'ny2' : 1,
        'nz2' : 0,
        'nx3' : 0,
        'ny3' : 1,
        'nz3' : 0,
        'u1' : uv_max2,
        'v1' : uv_min,
        'u2' : uv_max2,
        'v2' : uv_max,
        'u3' : uv_min2,
        'v3' : uv_min,
    },
    # triangle 10
    {
        'x1' : -64,
        'y1' : -64,
        'z1' : 64,
        'x2' : 64,
        'y2' : -64,
        'z2' : -64,
        'x3' : 64,
        'y3' : -64,
        'z3' : 64,
        'nx1' : 0,
        'ny1' : 1,
        'nz1' : 0,
        'nx2' : 0,
        'ny2' : 1,
        'nz2' : 0,
        'nx3' : 0,
        'ny3' : 1,
        'nz3' : 0,
        'u1' : uv_min2,
        'v1' : uv_min,
        'u2' : uv_max2,
        'v2' : uv_max,
        'u3' : uv_min2,
        'v3' : uv_max,
    },
]

# vertex rotation matrix to tilt forward 30 degrees
# v_rotation_matrix = np.array([
#     [1, 0, 0],
#     [0, np.cos(np.pi / 6), -np.sin(np.pi / 6)],
#     [0, np.sin(np.pi / 6), np.cos(np.pi / 6)]
# ])
v_rotation_matrix = rotation_matrix_x
# apply  to all vertices
for tri in tris:
    for i in range(1, 4):
        v = np.array([tri['x{}'.format(i)], tri['y{}'.format(i)]+128, tri['z{}'.format(i)]])
        v = v_rotation_matrix.dot(v)
        tri['x{}'.format(i)] = v[0]
        tri['y{}'.format(i)] = v[1]
        tri['z{}'.format(i)] = v[2]

mem = {
    # write rotation matrix to memory
    40000 : rotation_matrix[0, 0].astype(np.float16),
    40032 : rotation_matrix[0, 1].astype(np.float16),
    40064 : rotation_matrix[0, 2].astype(np.float16),
    40128 : rotation_matrix[1, 1].astype(np.float16),
    40160 : rotation_matrix[1, 2].astype(np.float16),
    40192 : rotation_matrix[2, 0].astype(np.float16),
    40224 : rotation_matrix[2, 1].astype(np.float16),
    40256 : rotation_matrix[2, 2].astype(np.float16),

    # triangle data
    # light direction
    47904 : 0.5, # x
    47936 : 0.707, # y
    47968 : 0.5, # z
}
tri_start = 48000
for tri in tris:
    mem[tri_start + 0] = tri['x1']
    mem[tri_start + 32] = tri['y1']
    mem[tri_start + 64] = tri['z1']
    mem[tri_start + 96] = tri['x2']
    mem[tri_start + 128] = tri['y2']
    mem[tri_start + 160] = tri['z2']
    mem[tri_start + 192] = tri['x3']
    mem[tri_start + 224] = tri['y3']
    mem[tri_start + 256] = tri['z3']
    mem[tri_start + 288] = tri['u1']
    mem[tri_start + 320] = tri['u2']
    mem[tri_start + 352] = tri['u3']
    mem[tri_start + 384] = tri['v1']
    mem[tri_start + 416] = tri['v2']
    mem[tri_start + 448] = tri['v3']
    mem[tri_start + 480] = tri['nx1']
    mem[tri_start + 512] = tri['nx2']
    mem[tri_start + 544] = tri['nx3']
    mem[tri_start + 576] = tri['ny1']
    mem[tri_start + 608] = tri['ny2']
    mem[tri_start + 640] = tri['ny3']
    mem[tri_start + 672] = tri['nz1']
    mem[tri_start + 704] = tri['nz2']
    mem[tri_start + 736] = tri['nz3']
    tri_start += 768

# # write rotation matrix to memory
# address = 40000
# memory[address:address+32] = [np.uint16(np.float16(rotation_matrix[0, 0]).view('H'))] * 32
# memory[address+32:address+32+32] = [np.uint16(np.float16(rotation_matrix[0, 1]).view('H'))] * 32
# memory[address+64:address+64+32] = [np.uint16(np.float16(rotation_matrix[0, 2]).view('H'))] * 32
# memory[address+96:address+96+32] = [np.uint16(np.float16(rotation_matrix[1, 0]).view('H'))] * 32
# memory[address+128:address+128+32] = [np.uint16(np.float16(rotation_matrix[1, 1]).view('H'))] * 32
# memory[address+160:address+160+32] = [np.uint16(np.float16(rotation_matrix[1, 2]).view('H'))] * 32
# memory[address+192:address+192+32] = [np.uint16(np.float16(rotation_matrix[2, 0]).view('H'))] * 32
# memory[address+224:address+224+32] = [np.uint16(np.float16(rotation_matrix[2, 1]).view('H'))] * 32
# memory[address+256:address+256+32] = [np.uint16(np.float16(rotation_matrix[2, 2]).view('H'))] * 32

# # triangle data
# address = 48000
# # light direction
# memory[address-96:address-96+32] = [np.uint16(np.float16(0.5).view('H'))] * 32 # x
# memory[address-64:address-64+32] = [np.uint16(np.float16(0.707).view('H'))] * 32 # y
# memory[address-32:address-32+32] = [np.uint16(np.float16(0.5).view('H'))] * 32 # z
# # triangle 1
# # note that the coordinates are in half-precision floating-point
# # they are stored 32 times so a vector register can hold them
# memory[address+  0:address+  0+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # x1
# memory[address+ 32:address+ 32+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # y1
# memory[address+ 64:address+ 64+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # z1
# memory[address+ 96:address+ 96+32] = [np.uint16(np.float16(64).view('H'))] * 32 # x2
# memory[address+128:address+128+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # y2
# memory[address+160:address+160+32] = [np.uint16(np.float16(0).view('H'))] * 32 # z2
# memory[address+192:address+192+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # x3
# memory[address+224:address+224+32] = [np.uint16(np.float16(64).view('H'))] * 32 # y3
# memory[address+256:address+256+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # z3
# # uv coordinates are in the range [0, 1] and are stored as half-precision floating-point numbers
# # however, they are stored 32 times in a row so a vector register can hold them
# memory[address+288:address+288+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # u1
# memory[address+320:address+320+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # u2
# memory[address+352:address+352+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # u3
# memory[address+384:address+384+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # v1
# memory[address+416:address+416+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # v2
# memory[address+448:address+448+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # v3
# # vertex normals
# memory[address+480:address+480+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx1
# memory[address+512:address+512+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx2
# memory[address+544:address+544+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx3
# memory[address+576:address+576+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny1
# memory[address+608:address+608+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny2
# memory[address+640:address+640+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny3
# memory[address+672:address+672+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz1
# memory[address+704:address+704+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz2
# memory[address+736:address+736+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz3
# address += 768
# # triangle 2
# memory[address+  0:address+  0+32] = [np.uint16(np.float16(64).view('H'))] * 32 # x1
# memory[address+ 32:address+ 32+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # y1
# memory[address+ 64:address+ 64+32] = [np.uint16(np.float16(0).view('H'))] * 32 # z1
# memory[address+ 96:address+ 96+32] = [np.uint16(np.float16(64).view('H'))] * 32 # x2
# memory[address+128:address+128+32] = [np.uint16(np.float16(64).view('H'))] * 32 # y2
# memory[address+160:address+160+32] = [np.uint16(np.float16(0).view('H'))] * 32 # z2
# memory[address+192:address+192+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # x3
# memory[address+224:address+224+32] = [np.uint16(np.float16(64).view('H'))] * 32 # y3
# memory[address+256:address+256+32] = [np.uint16(np.float16(-64).view('H'))] * 32 # z3
# # uv coordinates are in the range [0, 1] and are stored as half-precision floating-point numbers
# # however, they are stored 32 times in a row so a vector register can hold them
# memory[address+288:address+288+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # u1
# memory[address+320:address+320+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # u2
# memory[address+352:address+352+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # u3
# memory[address+384:address+384+32] = [np.uint16(np.float16(-0.5).view('H'))] * 32 # v1
# memory[address+416:address+416+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # v2
# memory[address+448:address+448+32] = [np.uint16(np.float16(15.49).view('H'))] * 32 # v3
# # vertex normals
# memory[address+480:address+480+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx1
# memory[address+512:address+512+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx2
# memory[address+544:address+544+32] = [np.uint16(np.float16(0).view('H'))] * 32 # nx3
# memory[address+576:address+576+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny1
# memory[address+608:address+608+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny2
# memory[address+640:address+640+32] = [np.uint16(np.float16(0).view('H'))] * 32 # ny3
# memory[address+672:address+672+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz1
# memory[address+704:address+704+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz2
# memory[address+736:address+736+32] = [np.uint16(np.float16(1).view('H'))] * 32 # nz3
