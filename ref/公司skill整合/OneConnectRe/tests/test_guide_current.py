import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GuideCurrent(unittest.TestCase):
 def test_generated_guide_has_current_interfaces(self):
  subprocess.run([sys.executable,str(ROOT/'tools/build_guide.py')],cwd=str(Path.home()),check=True,capture_output=True,text=True)
  html=(ROOT/'迭代接口手册.html').read_text(encoding='utf8')
  for text in ('8×10','setAdProvider','激励广告生命周期','oneConnectRewardLifecycle','game.round_ready'):
   self.assertTrue(text in html,text)
  self.assertIn('href="#section7"',html)
