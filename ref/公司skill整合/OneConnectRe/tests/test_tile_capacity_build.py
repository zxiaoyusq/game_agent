import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CapacityBuild(unittest.TestCase):
 def test_compiler_adds_reserve_frames_and_rejects_missing_atlas(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);game=root/'game';(game/'images').mkdir(parents=True);config=root/'levels.json';board=[[0]*12 for _ in range(6)];board[0][0]=board[0][1]=30;config.write_text(json.dumps({'levels':[{'level':13,'seconds':180,'board':board}]}),encoding='utf8');dest=game/'data.js';dest.write_bytes(b'untouched')
   cmd=[sys.executable,str(ROOT/'tools/compile_levels.py'),'--config',str(config),'--output',str(dest)];bad=subprocess.run(cmd,capture_output=True);self.assertNotEqual(bad.returncode,0);self.assertEqual(dest.read_bytes(),b'untouched')
   atlas=game/'images/tiles-reserve-test.png';atlas.write_bytes(b'not a png');bad=subprocess.run(cmd,capture_output=True);self.assertNotEqual(bad.returncode,0);self.assertEqual(dest.read_bytes(),b'untouched')
   atlas.write_bytes((ROOT/'game/images/tiles-reserve-test.png').read_bytes())
   ok=subprocess.run(cmd,capture_output=True);self.assertEqual(ok.returncode,0,ok.stderr.decode(errors='replace'));data=json.loads(dest.read_text(encoding='utf8'));anims=data['project'][3][5][7];self.assertTrue(all(len(a[7])==30 and a[7][29][0]=='images/tiles-reserve-test.png' for a in anims))
if __name__=='__main__':unittest.main()
