import json,unittest
from pathlib import Path
class FifthLevelReference(unittest.TestCase):
 def test_level_five_observed_contract(self):
  r=next((x for x in json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'] if x['level']==5),None);self.assertIsNotNone(r,'level 5 must be configured');self.assertEqual(r['seconds'],130);self.assertEqual(r['theme'],1);self.assertEqual(r['generator']['typeCount'],9);self.assertEqual(r['movement'],'static');screen=[[r['generator']['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertEqual(sum(map(sum,screen)),40);self.assertTrue(all(sum(row)==5 for row in screen[2:10]));self.assertTrue(all(sum(row)==0 for row in screen[:2]+screen[10:]))
