import json
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'monitor'))
from rng import next_seed, distance, method_j, method1, birds, is_shiny

class RNGTests(unittest.TestCase):
    def test_golden_models(self):
        for v in json.loads((ROOT/'tests/vectors.json').read_text()):
            with self.subTest(vector=v):
                p=method_j(int(v['seed'],16),v['sync']) if v['mode']=='stationary' else method1(int(v['seed'],16),v['offset'])
                for key in ('pid','nature','ivs'):self.assertEqual(p[key],v[key])

    def test_distance_roundtrip(self):
        random.seed(100)
        for _ in range(30):
            s=random.getrandbits(32);n=random.randrange(3000);end=s
            for _ in range(n):end=next_seed(end)
            self.assertEqual(distance(s,end),n)
        self.assertEqual(distance(0,0),0)
        self.assertEqual(distance(next_seed(0),0),0xffffffff)

    def test_native_bird_calibration(self):
        rows=birds(0x7e6d9b06,12345,54321)
        self.assertEqual([x['pid'] for x in rows],['5980A68B','6B6A463F','1D03049D'])
        self.assertEqual([x['route_index'] for x in rows],[14,11,20])
        self.assertEqual(birds(0x7e6d9b06,12345,54321,slots=()),[])

    def test_shiny_boundary(self):
        for low in range(10):self.assertEqual(is_shiny(low,0,0),low<8)
        self.assertTrue(is_shiny((12345^54321)<<16,12345,54321))

    def test_reader_profiles_are_exact(self):
        from reader import PROFILES
        self.assertEqual(len(PROFILES),2)
        self.assertTrue(all(len(h)==64 for h in PROFILES))
        source=(ROOT/'monitor/reader.py').read_text()
        for forbidden in ('WriteProcessMemory','VirtualAllocEx','CreateRemoteThread','SendInput','PROCESS_ALL_ACCESS'):
            self.assertNotIn(forbidden,source)

if __name__=='__main__':unittest.main()
