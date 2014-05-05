#!/usr/bin/env python3
# import os
# import sys
# parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, parentdir)
import time
import serial
import unittest
from codebug_loader.core import (CodeBug, CodeBugRaw)
from codebug_loader.char_map import (CharSprite, StringSprite)


class TestCodeBugRawObject(unittest.TestCase):

    def setUp(self):
        self.codebug = CodeBug(serial.Serial('/dev/ttyACM0'))
        # self.codebug = CodeBugRaw(serial.Serial('/dev/pts/4'))
        self.num_channels = 5

    # @unittest.skip
    def test_channels(self):
        """
            >>> codebug.channels[1].value = 2
            >>> codebug.channels[1].value
            2
        """
        for i in range(self.num_channels):
            self.codebug.channels[i].value = (i*i) % 0x1F

        for i in range(self.num_channels):
            self.assertEqual(self.codebug.channels[i].value, (i*i) % 0x1F)

    # @unittest.skip
    def test_channels_get_set(self):
        """
            >>> codebug.set(1, 2)
            >>> codebug.get(1)
            2
        """
        for i in range(self.num_channels):
            self.codebug.set(i, (i*i) % 0x1F)

        for i in range(self.num_channels):
            self.assertEqual(self.codebug.get(i), (i*i) % 0x1F)

        # with or_mask
        for i in range(self.num_channels):
            self.codebug.set(i, 0x10, or_mask=True)

        for i in range(self.num_channels):
            self.assertEqual(self.codebug.get(i), (0x10 | (i*i)) % 0x1F)

    # @unittest.skip
    def test_channel_get_set_bulk(self):
        """
            >>> codebug.set_bulk(0, [1, 2, 3])
            >>> codebug.channels[1].value
            2
        """
        v = list(range(self.num_channels))
        self.codebug.set_bulk(0, v)
        self.assertEqual(tuple(self.codebug.get_bulk(0, len(v))),
                         tuple(v))

        v[2] = 0b11011
        v[3] = 0b01001
        self.codebug.set_bulk(2, v[2:4])
        self.assertEqual(tuple(self.codebug.get_bulk(0, self.num_channels)),
                         tuple(v))

        v = list(range(self.num_channels))
        self.codebug.set_bulk(0, v)
        self.assertEqual(tuple(self.codebug.get_bulk(0, len(v))),
                         tuple(v))

        v[2] |= 0b10001
        v[3] |= 0b01001
        self.codebug.set_bulk(2, v[2:4], or_mask=True)
        self.assertEqual(tuple(self.codebug.get_bulk(0, self.num_channels)),
                         tuple(v))

    def test_channel_get_set_bulk(self):
        x = self.codebug.get(5)
        a = (x >> 4) & 0x1
        b = (x >> 5) & 0x1
        print("A is {}, B is {}".format(a, b))


    # @unittest.skip
    # def test_channel_read_write(self):
    #     """
    #         >>> codebug.write(0x300, data)
    #         >>> codebug.read(0x300, 0x400)
    #     """
    #     v = list(range(self.num_channels))
    #     self.codebug.set_bulk(0, v)
    #     self.assertEqual(self.codebug.get_bulk(0, len(v)), v)

    #     v[2] = 0b01101
    #     v[3] = 0b01011
    #     self.codebug.set_bulk(2, v[2:4])
    #     self.assertEqual(self.codebug.get_bulk(0, self.num_channels),
    #                      v)

class TestCodeBug(unittest.TestCase):

    def test_write_text(self):
        cb = CodeBug()
        msg = "Hello, CodeBug!"
        delay = 0.025
        for i in range(len(msg) * 5 + 5):
            cb.write_text(5 - i, 0, msg)
            time.sleep(delay)

        for i in range(len(msg) * 6 + 6):
            cb.write_text(0, i - 5, msg, direction="down")
            time.sleep(delay)

        for i in range(len(msg) * 5 + 5):
            cb.write_text(0 - i, 0, msg, direction="left")
            time.sleep(delay)

        for i in range(len(msg) * 6 + 6):
            cb.write_text(0, i - 5, msg, direction="up")
            time.sleep(delay)


class TestSprites(unittest.TestCase):

    def test_string_sprite(self):
        s = StringSprite("hello")

        expected = [[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
                    [1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
                    [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
                    [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0]]
        self.assertEqual(s.led_state, expected)


if __name__ == "__main__":
    unittest.main()
