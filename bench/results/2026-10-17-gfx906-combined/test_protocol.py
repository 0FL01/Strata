import copy
import unittest
import protocol as p

def log(arm='A',tail='chunk=4096 experts_streamed=16000'):
    return ('INFO context=262144 kv=int8 vram_free_mib=200 engine=test\nREADY 262144 stop\nRESUME 0\n'
            'PP 4096 65536 100 40\nPP 65535 65536 1000 65\nREUSED 0\n'+
            'T 1\n'*1024+f'DONE 1024 65536 {1000 if arm=="A" else 950} 100 length 0 0 0 0 0 4 0 0.0 65536 0 {tail}\n')

class TestProtocol(unittest.TestCase):
    def rows(self):return [dict(pair=i,arm=a,**p.parse(log(a))) for i,o in enumerate(p.ORDER,1) for a in o]
    def test_summary(self):self.assertAlmostEqual(p.summary(self.rows())['metrics']['PP']['paired_geomean_gain_pct'],100*(1000/950-1))
    def test_old_done_rejected(self):
        with self.assertRaises(ValueError):p.parse(log(tail=''))
    def test_chain_done_rejected(self):
        with self.assertRaises(ValueError):p.parse(log(tail='0 0 0 0 0 chunk=4096 experts_streamed=16000'))
    def test_counter_mismatch(self):
        r=self.rows();r[-1]['counters']['experts_streamed']='42'
        with self.assertRaises(ValueError):p.summary(r)
    def test_tokens_mismatch(self):
        r=self.rows();r[-1]['token_sha256']='wrong'
        with self.assertRaises(ValueError):p.summary(r)
    def test_layout_mismatch(self):
        r=self.rows();r[-1]['info']['kv']='f16'
        with self.assertRaises(ValueError):p.summary(r)
    def test_extra_output(self):
        with self.assertRaises(ValueError):p.parse(log()+'T 2\n')
    def test_nan(self):
        with self.assertRaises(ValueError):p.parse(log().replace('1000 100 length','nan 100 length'))
    def test_reused(self):
        with self.assertRaises(ValueError):p.parse(log().replace('RESUME 0','RESUME 1'))
    def test_info_after_ready(self):
        text=log();a,b,*rest=text.splitlines()
        with self.assertRaises(ValueError):p.parse('\n'.join([b,a]+rest)+'\n')
    def test_info_volatile(self):
        self.assertEqual(p.parse(log())['info'],p.parse(log().replace('vram_free_mib=200','vram_free_mib=350'))['info'])
if __name__=='__main__':unittest.main()
