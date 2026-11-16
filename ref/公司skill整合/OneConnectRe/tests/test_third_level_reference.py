import json,unittest
from pathlib import Path
class ThirdLevelReference(unittest.TestCase):
 def test_level_three_observed_contract(self):
  rows=json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'];r=next((x for x in rows if x['level']==3),None);self.assertIsNotNone(r,'level 3 must be configured');self.assertEqual(r['seconds'],163);self.assertIsNot(r.get('timed'),False);self.assertEqual(r['theme'],1);self.assertEqual(r['generator']['typeCount'],10);self.assertEqual(r['movement'],'static');screen=[[r['generator']['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertEqual(sum(map(sum,screen)),40);self.assertTrue(all(sum(row)==5 for row in screen[2:10]));self.assertTrue(all(sum(row)==0 for row in screen[:2]+screen[10:]))
