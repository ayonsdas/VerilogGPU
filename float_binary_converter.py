def float_to_binary(f):
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

def binary_to_float(f):
    if (f == "0000000000000000"):
        return 0.0
    exponent = 0
    for i in range(1, 6):
        exponent = exponent * 2 + (1 if f[i] == "1" else 0)
    exponent -= 16
    result = 1.0
    for i in range(6, 16):
        result = result * 2 + (1 if f[i] == "1" else 0)
    return (1 if f[0] == "0" else -1) * result * (2 ** (exponent - 10))
