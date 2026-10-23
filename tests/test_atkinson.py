import concurrent.futures
import sys
import unittest
from atkinson import atk


def reference(w, h, data):
    pixels = bytearray(data)
    for y in range(h):
        for x in range(w):
            i = y*w+x
            old = pixels[i]
            pixels[i] = 255 if old >= 128 else 0
            err = (old-pixels[i]) >> 3
            for dx, dy in ((1,0),(2,0),(-1,1),(0,1),(1,1),(0,2)):
                if 0 <= x+dx < w and y+dy < h:
                    j=(y+dy)*w+x+dx
                    pixels[j]=min(255,max(0,pixels[j]+err))
    return bytes(pixels)


class AtkinsonTest(unittest.TestCase):
    def test_dither_matches_reference_without_mutating_input(self):
        for w,h in ((1,1),(2,3),(3,2),(32,24)):
            data=bytes((i*37+11)%256 for i in range(w*h))
            original=bytes(bytearray(data));lookup={data: 68}
            self.assertEqual(atk(w,h,data),reference(w,h,data))
            self.assertEqual(data,original)
            self.assertEqual(lookup[original],68)

    def test_parallel_calls_share_immutable_input(self):
        data=bytes((i*37+11)%256 for i in range(64*48))
        original=bytes(bytearray(data));expected=reference(64,48,data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outputs=list(pool.map(lambda _: atk(64,48,data),range(128)))
        self.assertEqual(outputs,[expected]*128)
        self.assertEqual(data,original)
        if hasattr(sys,'_is_gil_enabled'):
            self.assertFalse(sys._is_gil_enabled())

    def test_empty_and_invalid_dimensions(self):
        self.assertEqual(atk(0,0,b''),b'')
        for w,h,data in ((-1,-1,b'x'),(-1,0,b''),(1,-1,b''),(2,3,b'x'),(sys.maxsize,2,b'')):
            with self.subTest(w=w,h=h),self.assertRaises(ValueError):
                atk(w,h,data)


if __name__ == '__main__':
    unittest.main()
