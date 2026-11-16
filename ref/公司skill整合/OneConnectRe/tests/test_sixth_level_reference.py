import json,unittest
from pathlib import Path
class SixthLevelReference(unittest.TestCase):
 def test_level_six(self):
  r=next((x for x in json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'] if x['level']==6),None);self.assertIsNotNone(r,'level 6 must be configured');self.assertEqual(r['seconds'],163);self.assertEqual(r['movement'],'gravity_down');self.assertEqual(r['gravity'],{'top':3,'left':0,'rows':6,'cols':6});self.assertEqual(r['generator']['typeCount'],9);self.assertNotIn('seed',r['generator']);screen=[[r['generator']['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertEqual([''.join(str(x) for x in row) for row in screen[3:9]],['001100','011110','111111','111111','011110','001100']);self.assertEqual(sum(map(sum,screen)),24)
