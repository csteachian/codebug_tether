import os
import time
import serial
import struct
import codebug_tether.packets
from codebug_tether.char_map import (char_map, StringSprite)


DEFAULT_SERIAL_PORT = '/dev/ttyACM0'
INPUT_CHANNEL_INDEX = 5


class CodeBugRaw(object):
    """Represents a CodeBug. Doesn't have fancy easy-to-use features."""

    class Channel(object):
        """A channel on a CodeBug."""
        def __init__(self, index, codebug_inst):
            self.index = index
            self.cbinst = codebug_inst

        @property
        def value(self):
            return self.cbinst.get(self.index)

        @value.setter
        def value(self, v):
            self.cbinst.set(self.index, v)

    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.channels = [self.Channel(i, self) for i in range(6)]

    def get(self, index):
        get_packet = codebug_tether.packets.GetPacket(index)
        return tx_rx_packet(get_packet, self.serial_port)

    def set(self, index, v, or_mask=False):
        set_packet = codebug_tether.packets.SetPacket(index, v, or_mask)
        tx_rx_packet(set_packet, self.serial_port)

    def get_bulk(self, start_index, length):
        get_bulk_pkt = codebug_tether.packets.GetBulkPacket(start_index,
                                                            length)
        return tx_rx_packet(get_bulk_pkt, self.serial_port)

    def set_bulk(self, start_index, values, or_mask=False):
        set_bulk_pkt = codebug_tether.packets.SetBulkPacket(start_index,
                                                            values,
                                                            or_mask)
        tx_rx_packet(set_bulk_pkt, self.serial_port)


class CodeBug(CodeBugRaw):
    """Adds fancy, easy-to-use features to CodeBugRaw."""

    def __init__(self, serial_port=DEFAULT_SERIAL_PORT):
        super(CodeBug, self).__init__(serial.Serial(serial_port))

    def get_input(self, switch):
        if isinstance(switch, str):
            switch = 4 if 'a' in switch.lower() else 5  # A is 4, B is 5
        return (self.get(INPUT_CHANNEL_INDEX) >> switch) & 0x1

    def clear(self):
        """Clears the LED's on CodeBug."""
        for row in range(5):
            self.set_row(row, 0)

    def set_row(self, row, val):
        """Sets a row of LEDs on CodeBug."""
        self.set(row, val)

    def get_row(self, row):
        """Returns a row of LEDs on CodeBug."""
        return self.get(row)

    def set_col(self, col, val):
        """Sets an entire column of LEDs on CodeBug."""
        # TODO add and_mask into set packet
        for row in range(5):
            state = (val >> (4 - row)) & 0x1  # state of column 1/0
            mask = 1 << (4 - col)  # bit mask to apply to row
            if state > 0:
                self.set(row, mask, or_mask=True)  # OR row with mask
            else:
                # TODO and_mask here
                mask ^= 0x1f
                self.set(row, self.get(row) & mask)  # AND row with mask

    def get_col(self, col):
        """Returns an entire column of LEDs on CodeBug."""
        c = 0
        for row in range(5):
            c |= (self.get_row(row) >> (4 - col)) << (4-row)
        return c

    def set_led(self, x, y, state):
        """Sets an LED on CodeBug."""
        mask = 1 << (4 - x)  # bit mask to apply to row
        if state > 0:
            self.set(y, mask, or_mask=True)  # OR row with mask
        else:
            # TODO and_mask here
            mask ^= 0x1f
            self.set(y, self.get(y) & mask)  # AND row with mask

    def get_led(self, x, y):
        """Returns the state of an LED on CodeBug."""
        return (self.get(y) >> (4 - x)) & 0x1

    def write_text(self, x, y, message, direction="right"):
        """Writes some text on CodeBug at LED (x, y)."""
        s = StringSprite(message, direction)
        self.clear()
        for row_i, row in enumerate(s.led_state):
            if (row_i - y) >= 0 and (row_i - y) <= 4:
                code_bug_led_row = 0
                for col_i, state in enumerate(row):
                    if col_i + x >= 0 and col_i + x <= 4:
                        code_bug_led_row |= state << 4 - (col_i + x)
                self.set(4-row_i+y, code_bug_led_row)


def tx_rx_packet(packet, serial_port):
    """Sends a packet and waits for a response."""
    # print("Writing {} ({})".format(packet, time.time()))
    # print("data", packet.to_bytes())
    serial_port.write(packet.to_bytes())
    if isinstance(packet, codebug_tether.packets.GetPacket):
        # just read 1 byte
        return struct.unpack('B', serial_port.read(1))[0]

    elif (isinstance(packet, codebug_tether.packets.SetPacket) or
          isinstance(packet, codebug_tether.packets.SetBulkPacket)):
        # just read 1 byte
        b = struct.unpack('B', serial_port.read(1))[0]
        assert (b == codebug_tether.packets.AckPacket.ACK_BYTE)

    elif isinstance(packet, codebug_tether.packets.GetBulkPacket):
        return struct.unpack('B'*packet.length,
                             serial_port.read(packet.length))
