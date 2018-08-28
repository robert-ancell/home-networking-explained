#!/usr/bin/python3

from bitfuncs import *

def encode_4b5b (data):
    map = [ 0b11110, 0b01001, 0b10100, 0b10101,
            0b01010, 0b01011, 0b01110, 0b01111,
            0b10010, 0b10011, 0b10110, 0b10111,
            0b11010, 0b11011, 0b11100, 0b11101 ]
    d = []
    for offset in range (0, len (data), 4):
        i = bits_to_int (data[offset:offset + 4])
        d += int_to_bits (map[i], 5)
    return d

def generate_4b5b_idle (count = 1):
    return [1, 1, 1, 1, 1] * count

def generate_4b5b_start_of_stream_delimiter ():
    return [1, 1, 0, 0, 0, 1, 0, 0, 0, 1]

def generate_4b5b_end_of_stream_delimiter ():
    return [0, 1, 1, 0, 1, 0, 0, 1, 1, 1]

class Scrambler:
    def __init__ (self):
        self.bits = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        for i in range (10):
            self.next_bit ()

    def next_bit (self):
        bit = self.bits[8] ^ self.bits[10]
        self.bits = [bit] + self.bits[:-1]
        return bit

    def scramble (self, data):
        out = []
        for bit in data:
            out.append (bit ^ self.next_bit ())
        return out

def encode_nrzi (data):
    bits = []
    level = 0 # FIXME: Check
    for bit in data:
        if bit == 1:
            level = level ^ 1
        bits.append (level)
    return bits

def encode_mlt_3 (data):
    levels = [-1, 0, 1, 0]
    index = 0
    signal = []
    for bit in data:
        if bit == 1:
            index = (index + 1) % 4
        signal.append (levels[index])
    return signal

def make_ethernet2_preamble ():
    return int_to_bits (0b10101010, 8) * 7

def make_ethernet2_start_frame_delimiter ():
    return int_to_bits (0b10101011, 8)

def make_crc32 (data):
    d = data + [0] * 32
    polynomial = [ 1,
                   0, 0, 0, 0,
                   0, 1, 0, 0,
                   1, 1, 0, 0,
                   0, 0, 0, 1,
                   0, 0, 0, 1,
                   1, 1, 0, 1,
                   1, 0, 0, 1,
                   0, 1, 1, 1 ]

    while True:
        offset = 0
        while d[offset] != 1:
            offset += 1
            if offset + 32 >= len (d):
                return d[-32:]
        for (o, b) in enumerate (polynomial):
            d[offset + o] ^= b

def make_ethernet_padding (payload):
    # Minimum payload is 46 octets
    padding = max ((46 * 8) - len (payload), 0)
    return [0] * padding

def make_arp_packet (hardware_type, protocol_type, operation, sender_hardware_address, sender_protocol_address, target_hardware_address, target_protocol_address):
    assert (len (sender_hardware_address) == len (target_hardware_address))
    assert (len (sender_protocol_address) == len (target_protocol_address))
    return int_to_bits (hardware_type, 16) +\
           int_to_bits (protocol_type, 16) +\
           int_to_bits (len (sender_hardware_address), 8) +\
           int_to_bits (len (sender_protocol_address), 8) +\
           int_to_bits (operation, 16) +\
           bytes_to_bits (sender_hardware_address) +\
           bytes_to_bits (sender_protocol_address) +\
           bytes_to_bits (target_hardware_address) +\
           bytes_to_bits (target_protocol_address)

ETHERTYPE_IP  = 0x0800
ETHERTYPE_ARP = 0x0806

HARDWARE_TYPE_ETHERNET = 1

ARP_OPERATION_REQUEST = 1
ARP_OPERATION_REPLY   = 2

def parse_mac (text):
    data = bytes ()
    octets = text.split (':')
    assert (len (octets) == 6)
    for o in octets:
        assert (len (o) == 2)
        data += bytes([int (o[0], 16), int (o[1], 16)])
    return data

def parse_ipv4_address (text):
    data = bytes ()
    octets = text.split ('.')
    assert (len (octets) == 4)
    for o in octets:
        v = int (o)
        assert (v >= 0 and v <= 255)
        data += bytes([v])
    return data

source_mac = parse_mac ('80:00:20:20:3A:AE')
source_ipv4_address = parse_ipv4_address ('192.168.0.2')
destination_mac = parse_mac ('80:00:20:7A:3F:3E')
destination_ipv4_address = parse_ipv4_address ('192.168.0.1')

arp_packet = make_arp_packet (HARDWARE_TYPE_ETHERNET, ETHERTYPE_IP, ARP_OPERATION_REQUEST, source_mac, source_ipv4_address, destination_mac, destination_ipv4_address)
padding = make_ethernet_padding (arp_packet)
d_mac = bytes_to_bits (destination_mac)
s_mac = bytes_to_bits (source_mac)
ethertype = int_to_bits (ETHERTYPE_ARP, 16)
frame = d_mac + s_mac + ethertype + arp_packet + padding
crc = make_crc32 (frame)
preamble = make_ethernet2_preamble ()
sfd = make_ethernet2_start_frame_delimiter ()
packet = preamble + sfd + frame + crc
print (packet)
print (len (packet))
#signal = encode_mlt_3 (encode_nrzi (encode_4b5b (packet))) # FIXME: nrzi not needed - done in mlt_3?
# FIXME is this the required interpacket gap?
# FIXME variable name
encoded_packet = generate_4b5b_idle (6) + generate_4b5b_start_of_stream_delimiter () + encode_4b5b (packet) + generate_4b5b_end_of_stream_delimiter () + generate_4b5b_idle (6)
scrambler = Scrambler ()
scrambled_packet = scrambler.scramble (encoded_packet)
signal = encode_mlt_3 (scrambled_packet)
print (signal)

import cairo
import math

#pixel_duration = 0.5 # ns
pixel_duration = 4 # ns
pulse_duration = 8 # ns
pulse_width = pulse_duration / pixel_duration
microsecond_width = 1000 / pixel_duration
width = math.ceil (len (signal) * pulse_width)
height = 450
s = cairo.ImageSurface (cairo.FORMAT_RGB24, width, height)
c = cairo.Context (s)

# Fill background
c.set_source_rgb (1.0, 1.0, 1.0)
c.paint ()

def draw_box (c, x, y, width, height, r, g, b):
    c.rectangle (x, 0, width, y)
    c.set_source_rgba (r, g, b, 0.1)
    c.fill ()
    c.rectangle (x, y, width, height)
    c.set_source_rgb (r, g, b)
    c.fill ()
    return width


idle_width = 6 * 5 * pulse_width
ssd_width = 10 * pulse_width
esd_width = 10 * pulse_width

slow_pulse_width = pulse_width * 5 / 4.0
preamble_width = len (preamble) * slow_pulse_width
sfd_width = len (sfd) * slow_pulse_width
d_mac_width = len (d_mac) * slow_pulse_width
s_mac_width = len (s_mac) * slow_pulse_width
ethertype_width = len (ethertype) * slow_pulse_width
crc_width = len (crc) * slow_pulse_width
payload_width = len (arp_packet) * slow_pulse_width
padding_width = len (padding) * slow_pulse_width

def rgb (text):
    return (int (text[1:3], 16) / 255.0, int (text[3:5], 16) / 255.0, int (text[5:7], 16) / 255.0)

idle_colour = rgb ('#fce94f')
framing_colour = rgb ('#c4a000')

x  = draw_box (c, 0, 250, idle_width,      25, *idle_colour)
x += draw_box (c, x, 250, ssd_width,       25, *framing_colour)
x += draw_box (c, x, 300, preamble_width,  25, *rgb ('#fcaf3e'))
x += draw_box (c, x, 300, sfd_width,       25, *rgb ('#f57900'))
x += draw_box (c, x, 350, d_mac_width,     25, *rgb ('#8ae234'))
x += draw_box (c, x, 350, s_mac_width,     25, *rgb ('#4e9a06'))
x += draw_box (c, x, 350, ethertype_width, 25, *rgb ('#ad7fa8'))
x += draw_box (c, x, 400, payload_width,   25, *rgb ('#729fcf'))
x += draw_box (c, x, 350, padding_width,   25, *rgb ('#888a85'))
x += draw_box (c, x, 350, crc_width,       25, *rgb ('#ef2929'))
x += draw_box (c, x, 250, esd_width,       25, *framing_colour)
x += draw_box (c, x, 250, idle_width,      25, *idle_colour)

# Draw 1us timing lines
x = microsecond_width
c.set_line_width (1.0)
c.set_source_rgba (0, 0, 0, 0.25)
while x < width:
    c.move_to (x + 0.5, 0)
    c.rel_line_to (0, height)
    x += microsecond_width
c.stroke ()

last_level = -1
def level_to_y (level):
    return (1 - level) * 25 + 25 + 0.5
last_y = level_to_y (last_level)
c.move_to (0, last_y)
x = 0.5
for level in signal:
    y = level_to_y (level)
    c.line_to (x + pulse_width / 2, last_y)
    c.line_to (x + pulse_width / 2, y)
    c.line_to (x + pulse_width, y)
    last_y = y
    x += pulse_width
c.set_source_rgb (0.0, 0.0, 0.0)
c.set_line_width (1.0)
c.stroke ()

def render_binary (c, bits, pulse_width, pulse_height):
    last_bit = bits[0]
    if last_bit == 1:
        c.rel_move_to (0, -pulse_height)
    for bit in bits:
        if bit != last_bit:
            c.rel_line_to (0, pulse_height * (last_bit - bit))
        c.rel_line_to (pulse_width, 0)
        last_bit = bit

c.move_to (0.5, 125.5)
render_binary (c, scrambled_packet, pulse_width, 25)
c.set_source_rgb (0.0, 0.0, 0.0)
c.set_line_width (1.0)
c.stroke ()

c.move_to (0.5, 175.5)
render_binary (c, encoded_packet, pulse_width, 25)
c.set_source_rgb (0.0, 0.0, 0.0)
c.set_line_width (1.0)
c.stroke ()

c.move_to (0.5 + idle_width + ssd_width, 225.5)
render_binary (c, packet, slow_pulse_width, 25)
c.set_source_rgb (0.0, 0.0, 0.0)
c.set_line_width (1.0)
c.stroke ()

s.write_to_png ('graph.png')

# 3.3V or 2.8V?
