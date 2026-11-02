"""Differential checks against the retained exported controller, not race acceptance."""
import hashlib
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from sim_native import Controller, build


def adc(mask, outer=0):
    bits=[16,8,4,2,1]
    return [35 if (mask|outer)&bit else 500 for bit in bits]


@unittest.skipUnless(sys.platform=='win32','Differential sketch bridge currently requires Windows/MSVC')
class NativeParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=ROOT/'build-output/native-migration/parity'
        a,_=build(ROOT/'car.ino',folder/'exported')
        b,_=build(ROOT/'firmware/native_car/native_car.ino',folder/'handwritten')
        cls.original,cls.native=Controller(a),Controller(b)

    def compare(self, samples):
        self.original.reset();self.native.reset()
        digest=hashlib.sha256()
        count=0
        for ms,values in samples:
            expected=self.original.step(ms,values);actual=self.native.step(ms,values)
            a=self.original.state();b=self.native.state()
            # The rewritten core reports a fault enum, not a source-line number.
            a.pop('firstFaultLine');b.pop('firstFaultLine')
            self.assertEqual((actual,b),(expected,a),msg='at ms=%d ADC=%s'%(ms,values))
            digest.update(repr((ms,expected,a)).encode());count+=1
        return count,digest.hexdigest()

    def test_timed_phases_and_thresholds(self):
        sequences=[
            [(4,1200),(6,20),(4,40),(12,45),(4,200)],
            [(4,200),(8,50),(0,80),(8,35),(12,30),(4,100)],
            [(4,200),(2,50),(0,80),(2,35),(6,30),(4,100)],
            [(4,200),(8,50),(14,100),(8,100),(4,100)],
            [(4,200),(14,500),(4,200),(4,24000),(4,200),(14,300),(4,100)],
            [(4,200),(10,10),(4,10),(10,10),(4,100)],
            [(4,200),(0,115),(4,100)],
            [(4,200),(0,1200),(14,300),(4,100)],
        ]
        for sequence in sequences:
            samples=[];now=0
            for mask,duration in sequence:
                for _ in range(duration//5):now+=5;samples.append((now,adc(mask)))
            with self.subTest(sequence=sequence):self.compare(samples)
        samples=[(i*5,[v,v,35,v,v]) for i,v in enumerate([69,70,119,120,500]*20,1)]
        self.compare(samples)

    def test_raw_outer_confirmation_probe_and_reversal(self):
        for side in [1,16]:
            samples=[];now=0
            for mask,duration,outer in [(4,200,0),(0,15,side),(0,250,side),(8 if side==16 else 2,40,side),(4,200,0)]:
                for _ in range(duration//5):now+=5;samples.append((now,adc(mask,outer)))
            self.compare(samples)

    def test_millis_wrap_and_overall_deadline(self):
        for start in [0,0xffffff00]:
            self.compare([((start+i*5)&0xffffffff,adc(4)) for i in range(1,300)])
        self.compare([(5,adc(4)),(105,adc(4)),(180004,adc(4)),(180005,adc(4)),(180010,adc(14))])

    def test_seeded_sensor_sequences(self):
        rng=random.Random(20261103)
        for episode in range(100):
            samples=[];now=0
            masks=[0,2,4,6,8,12,14] if episode%2 else [0,2,4,6,8,10,12,14]
            for _ in range(80):
                mask=rng.choice(masks);outer=rng.choice([0,0,1,16,17])
                for _ in range(rng.randint(1,15)):
                    now+=rng.choice([1,2,5,10,20]);samples.append((now,adc(mask,outer)))
            with self.subTest(episode=episode):self.compare(samples)


if __name__=='__main__':unittest.main()
