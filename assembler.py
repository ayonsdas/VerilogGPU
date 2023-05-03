# adds s_rt, s_ra, s_rb
# subs s_rt, s_ra, s_rb
# muls s_rt, s_ra, s_rb
# divs s_rt, s_ra, s_rb
# add rt, ra, rb
# sub rt, ra, rb
# mul rt, ra, rb
# div rt, ra, rb
# mov rt, imm16
# movl rt, s_ra
# movidx rt
# movraw rt, s_ra
# movs s_rt, imm16
# ld rt, s_ra
# ldall rt, s_ra
# st s_rt, ra
# sts s_rt, ra
# pushmask
# popmask
# peekmask rt
# andmask ra
# andmasks s_ra
# invertmask
# jmpmask imm16
# jmpnotmask imm16
# and rt, ra, rb
# or rt, ra, rb
# not rt, ra
# gt rt, ra, rb
# lt rt, ra, rb
# gte rt, ra, rb
# lte rt, ra, rb
# ands s_rt, s_ra, s_rb
# ors s_rt, s_ra, s_rb
# nots s_rt, s_ra
# gts s_rt, s_ra, s_rb
# lts s_rt, s_ra, s_rb
# gtes s_rt, s_ra, s_rb
# ltes s_rt, s_ra, s_rb

import re
import imageio.v3 as imageio
import sys
import numpy as np
import float_binary_converter as fb
from data import mem

opMap ={"adds" : "00",
        "subs" : "01",
        "muls" : "02",
        "divs" : "03",
        "add" : "04",
        "sub" : "05",
        "mul" : "06",
        "div" : "07",
        "mov" : "08",
        "movl" : "09",
        "movidx" : "0A",
        "movraw" : "0B",
        "movs" : "0C",
        "movpart" : "0D",
        "ld" : "10",
        "ldall" : "11",
        "lds" : "12",
        "st" : "14",
        "sts" : "18",
        "wrscreen" : "1C",
        "pushmask" : "20",
        "popmask" : "21",
        "peekmask" : "22",
        "invertmask" : "24",
        "andmask" : "25",
        "andmasks" : "26",
        "jmpmask" : "28",
        "jmpnotmask" : "29",
        "ldtex32" : "50",
        "and" : "40",
        "or" : "41",
        "not" : "42",
        "gt" : "44",
        "lt" : "45",
        "gte" : "46",
        "lte" : "47",
        "ands" : "48",
        "ors" : "49",
        "nots" : "4A",
        "gts" : "4C",
        "lts" : "4D",
        "gtes" : "4E",
        "ltes" : "4F",
        "publish" : "54"
        }


def binToHexa(n):
    bnum = int(n)
    temp = 0
    mul = 1

    # counter to check group of 4
    count = 1

    # char array to store hexadecimal number
    hexaDeciNum = ['0'] * 100

    # counter for hexadecimal number array
    i = 0
    while bnum != 0:
        rem = bnum % 10
        temp = temp + (rem * mul)

        # check if group of 4 completed
        if count % 4 == 0:

            # check if temp < 10
            if temp < 10:
                hexaDeciNum[i] = chr(temp + 48)
            else:
                hexaDeciNum[i] = chr(temp + 55)
            mul = 1
            temp = 0
            count = 1
            i = i + 1

        # group of 4 is not completed
        else:
            mul = mul * 2
            count = count + 1
        bnum = int(bnum / 10)

    # check if at end the group of 4 is not
    # completed
    if count != 1:
        hexaDeciNum[i] = chr(temp + 48)

    # check at end the group of 4 is completed
    if count == 1:
        i = i - 1

    # printing hexadecimal number
    # array in reverse order
    hexa = ""
    while i >= 0:
        hexa += hexaDeciNum[i]
        i = i - 1
    return hexa


def float_to_half_precision(f):
    # Extract sign, exponent, and mantissa from the input float
    if f == 0.0:
        sign_bit = 0
        exponent_bits = 0
        mantissa_bits = 0
    else:
        sign_bit = 1 if f < 0 else 0
        f = abs(f)
        exponent = -16
        while exponent <= 15 and f >= (2 ** exponent):
            exponent += 1
        exponent -= 1
        exponent_bits = (exponent + 16) % 32
        mantissa_bits = int((f - 2 ** exponent) * (2 ** (10 - exponent)))

    # Combine the sign, exponent, and mantissa bits into a 16-bit half-precision number
    bits = abs((sign_bit << 15) | (exponent_bits << 10) | mantissa_bits)
    return '{:016b}'.format(bits)


class Assembler:

    @staticmethod
    def assemble(lines):
        f = open("mem.hex", "w")
        f.write("@0\n")
        pack = []

        for line in lines:
            val = ["", "", "", "", "", "", ""]
            # print(line, end="")
            line = re.split("[,\s]+", line)
            for i in range(1, len(line)):
                while line[i] and (line[i][0] < '0' or line[i][0] > '9'):
                    line[i] = line[i][1:]
                if line[0] == "mov" and i == 2:
                    line[i] = binToHexa(float_to_half_precision(float(line[i])))
                    while len(line[i]) < 4:
                        line[i] = "0" + line[i]
                else:
                    if len(line[i]) > 0:
                        line[i] = hex(int(line[i]))[2:].upper()
                    if (line[0] in ["movs"] and i == 2) or (line[0] in ["jmpmask", "jmpnotmask"] and i == 1):
                        while len(line[i]) < 4:
                            line[i] = "0" + line[i]
            # print(line)
            val[0] = opMap[line[0]]
            if line[0] in ["mov", "movs"]:
                val[1] = line[1]
                for i in range(4):
                    val[i + 2] = line[2][i]
                val[6] = '0'
            elif line[0] in ["jmpmask", "jmpnotmask"]:
                val[1] = '0'
                for i in range(4):
                    val[i + 2] = line[1][i]
                val[6] = '0'
            elif line[0] in ["st", "sts"]:
                val[1] = '0'
                for i in range(1, 3):
                    val[i + 1] = line[i]
                for i in range(3):
                    val[i + 4] = '0'
            elif line[0] in ["andmask", "andmasks"]:
                for i in range(1, 7):
                    val[i] = '0'
                val[2] = line[1]
            else:
                for i in range(1, min(7, len(line))):
                    if line[i]:
                        val[i] = line[i]
                    else:
                        val[i] = '0'
                for i in range(len(line), 7):
                    val[i] = "0"
            # print(val)
            # print("".join(val))
            # print()
            pack.append("".join(val))
            if len(pack) == 16:
                f.write("".join(pack) + "\n")
                pack = []
        while len(pack) < 16:
            pack.append("FFFFFFFF")
        f.write("".join(pack) + "\n")

        # import imageio
        # import numpy as np
        # mem start at 30,000
        f.write("@3E8\n")
        # Read minecraft.png
        img = imageio.imread("minecraft.png")

        # Extract the red channel as an array of uint8
        red = img[:, :, 0].reshape((len(img) * len(img[0]),)).astype(np.uint16)

        # Extract the green channel as an array of uint8
        green = img[:, :, 1].reshape((len(img) * len(img[0]),)).astype(np.uint16)

        # Extract the blue channel as an array of uint8
        blue = img[:, :, 2].reshape((len(img) * len(img[0]),)).astype(np.uint16)

        # write red hex
        for i in range(len(red)):
            bits = fb.float_to_binary(float(red[i] / 255.0))
            digits = '{:0{width}x}'.format(int(bits, 2), width=4).upper()
            f.write(digits + ("\n" if (i % 32 == 31) else ""))
        # write green hex
        for i in range(len(green)):
            bits = fb.float_to_binary(float(green[i] / 255.0))
            digits = '{:0{width}x}'.format(int(bits, 2), width=4).upper()
            f.write(digits + ("\n" if (i % 32 == 31) else ""))
        # write blue hex
        for i in range(len(blue)):
            bits = fb.float_to_binary(float(blue[i] / 255.0))
            digits = '{:0{width}x}'.format(int(bits, 2), width=4).upper()
            f.write(digits + ("\n" if (i % 32 == 31) else ""))
        
        prev_addr = 0
        for k, v in sorted(mem.items()):
            if k - prev_addr != 32:
                f.write('@{:0x}\n'.format(k // 32).upper())
            prev_addr = k
            hex_val = '{:0{width}x}'.format(int(fb.float_to_binary(v), 2), width=4).upper()
            f.write(hex_val * 32)
            f.write("\n")
        # f.write("@5D9\n")
        # light_start = -96
        # light = [0.5, 0.707, 0.5]
        
        # triangle1_start = 0
        # triange1 = [-64, -64, -64, 64, -64, 0, -64, 64, -64, -0.5, 15.49,
        #     -0.5, -0.5, -0.5, 15.49, 0, 0, 0, 0, 0, 0, 1, 1, 1]
        
        # triangle2_start = 768
        # triangle2 = [64, -64, 0, 64, 64, 0, -64, 64, -64, 15.49, 15.49,
        #     -0.5, -0.5, 15.49, 15.49, 0, 0, 0, 0, 0, 0, 1, 1, 1]
        # starts = [light_start, triangle1_start, triangle2_start]
        # info = [light, triange1, triangle2]
        # for start, vals in zip(starts, info):
        #     for val in vals:
        #         hex_val = '{:0{width}x}'.format(int(fb.float_to_binary(val), 2), width=4).upper()
        #         f.write(hex_val * 32)
        #         f.write("\n")
        
        # print instructions with line numbers starting from 0
        # for i in range(len(instructions)):
        #     print(str(i) + ": " + instructions[i])


myFile = open(sys.argv[1]).readlines()

a = Assembler()
a.assemble(myFile)
