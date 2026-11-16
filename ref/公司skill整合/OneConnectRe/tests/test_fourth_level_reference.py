import json,unittest
from pathlib import Path
class FourthLevelReference(unittest.TestCase):
 def test_level_four_observed_contract(self):
  r=next((x for x in json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'] if x['level']==4),None);self.assertIsNotNone(r,'level 4 must be configured');self.assertEqual(r['seconds'],243);self.assertEqual(r['theme'],1);self.assertEqual(r['generator']['typeCount'],11);self.assertEqual(r['movement'],'static');screen=[[r['generator']['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertEqual(sum(map(sum,screen)),50);self.assertTrue(all(sum(row)==5 for row in screen[1:11]));self.assertTrue(all(sum(row)==0 for row in screen[:1]+screen[11:]))
