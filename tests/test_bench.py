# -*- coding: utf-8 -*
# From https://gist.github.com/mnixry/3608d0207196b847887d34ace8feeb87
encoding, decoding = (
    lambda input_bytes: (
        "".join(
            chr(0x4E00 + sum(1 << i for i, bit in enumerate(reversed(row)) if bit))
            for row in (
                lambda x, length: (
                    tuple(next(it, None) for it in x) for _ in range(length)
                )
            )(
                [((char >> i) & 1 for char in input_bytes for i in reversed(range(8)))]
                * 14,
                len(input_bytes) * 4 // 7 + (1 if len(input_bytes) * 4 % 7 else 0),
            )
        )
        + (chr(0x3D00 + len(input_bytes) % 7) if len(input_bytes) % 7 else "")
    ),
    lambda input_string: bytes(
        sum(1 << i for i, bit in enumerate(reversed(row)) if bit)
        for row in (
            lambda raw_string, residue: (
                lambda x, length: (
                    tuple(next(it, None) for it in x) for _ in range(length)
                )
            )(
                [
                    (
                        (char >> i) & 1
                        for char in (ord(i) - 0x4E00 for i in raw_string)
                        for i in reversed(range(14))
                    )
                ]
                * 8,
                (len(raw_string) - 1) // 4 * 7 + (residue or 7),
            )
        )(
            input_string[
                : (
                    None
                    if input_string and 0x4E00 <= ord(input_string[-1]) <= 0x8DFF
                    else -1
                )
            ],
            (
                ord(input_string[-1]) - 0x3D00
                if input_string and 0 <= ord(input_string[-1]) - 0x3D00 < 8
                else 0
            ),
        )
    ),
)

import sys

sys.path.append(".")
import time
import unittest
from random import randint
from unittest import TestCase

import pybase16384 as bs


class TestBench(TestCase):
    def test_bench(self):
        start = time.time()
        value = b"="
        for i in range(1000):
            value += b"x"
            self.assertEqual(bs.decode_safe(bs.encode_safe(value)), value)
        end = time.time()
        print(f"C extension tooks {end - start} seconds")

        start = time.time()
        value = b"="
        for i in range(1000):
            value += b"x"
            self.assertEqual(decoding(encoding(value)), value)
        end = time.time()
        print(f"Pure python tooks {end - start} seconds")

    def test_bench2(self):
        value = b"xxx" * 1000000
        start = time.time()
        self.assertEqual(bs.decode_safe(bs.encode_safe(value)), value)
        end = time.time()
        ctime = end - start
        print(f"C extension tooks {ctime} seconds")

        start = time.time()
        buffer = bytearray(bs.encode_len(len(value)))
        buffer_updated = bs._encode_into_safe(value, buffer)
        buffer2 = bytearray(bs.decode_len(buffer_updated, 0))
        buffer_updated2 = bs._decode_into_safe(buffer[:buffer_updated], buffer2)
        end = time.time()
        self.assertEqual(bytes(buffer2[:buffer_updated2]), value)
        cztime = end - start
        print(f"C extension zerocopy tooks {cztime} seconds")

        start = time.time()
        self.assertEqual(decoding(encoding(value)), value)
        end = time.time()
        pytime = end - start
        print(f"Pure python tooks {pytime} seconds")

        print(f"C extension zerocopy is {pytime/cztime} times faster than pure python")


if __name__ == "__main__":
    unittest.main()
