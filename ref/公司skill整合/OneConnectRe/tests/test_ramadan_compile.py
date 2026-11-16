import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent


class RamadanCompile(unittest.TestCase):
    def test_requires_atlas_and_emits_theme(self):
        source=ROOT/'analysis/ui_iteration_candidate_v77/game/images/ramadan-tiles.webp'
        if not source.exists(): self.skipTest('candidate atlas not present')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); game=root/'game'; (game/'images').mkdir(parents=True)
            board=[[0]*12 for _ in range(6)];board[0][0]=board[0][1]=20
            config=root/'config.json';config.write_text(json.dumps({'levels':[{'level':1,'seconds':180,'theme':3,'board':board}]}),encoding='utf8')
            command=[sys.executable,'-X','utf8',str(ROOT/'tools/compile_levels.py'),'--config',str(config),'--output',str(game/'data.js')]
            missing=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
            self.assertNotEqual(missing.returncode,0)
            self.assertFalse((game/'data.js').exists())
            from PIL import Image
            Image.new('RGBA',(512,512),(0,0,0,0)).save(game/'images/ramadan-tiles.webp',format='WEBP',lossless=True)
            corrupt=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
            self.assertNotEqual(corrupt.returncode,0,'wrong atlas pixels must be rejected')
            self.assertFalse((game/'data.js').exists())
            shutil.copyfile(source,game/'images/ramadan-tiles.webp')
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads((game/'data.js').read_text(encoding='utf8'))
            self.assertEqual([(a[0],len(a[7])) for a in data['project'][3][5][7]], [('t0',20),('t1',20),('t2',20),('t3',20)])
            config.write_text(json.dumps({'levels':[{'level':1,'seconds':180,'theme':0,'board':board}]}),encoding='utf8')
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads((game/'data.js').read_text(encoding='utf8'))
            self.assertEqual(data['project'][3][5][7][-1][0], 't3', 'ordinary edits must preserve an installed theme')
            reserve=ROOT/'analysis/ui_iteration_candidate_v83/game/images/tiles-reserve-test.webp'
            if reserve.exists():
                shutil.copyfile(reserve,game/'images/tiles-reserve-test.webp')
                board[0][0]=board[0][1]=30
                config.write_text(json.dumps({'levels':[{'level':1,'seconds':180,'theme':0,'board':board}]}),encoding='utf8')
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
                self.assertEqual(result.returncode,0,result.stderr)
                data=json.loads((game/'data.js').read_text(encoding='utf8'))
                self.assertTrue(all(a[7][20][0]=='images/tiles-reserve-test.webp' for a in data['project'][3][5][7][:3]))


if __name__=='__main__': unittest.main()
