def int_to_bits (value, width):
    bits = []
    mask = 1 << (width - 1)
    while mask != 0:
        if value & mask == 0:
            bits.append (1)
        else:
            bits.append (0)
        mask >>= 1
    return bits

def bits_to_int (bits):
    value = 0
    for (i, b) in enumerate (reversed (bits)):
        value |= b << i
    return value

def bytes_to_bits (value):
    bits = []
    for octet in value:
        bits += int_to_bits (octet, 8)
    return bits
