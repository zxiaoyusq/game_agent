import json,unittest
from pathlib import Path
class SecondLevelReference(unittest.TestCase):
 def test_level_two_contract(self):
  rows=json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'];r=next((r for r in rows if r['level']==2),None);self.assertIsNotNone(r,'level 2 must be configured');self.assertEqual(r['seconds'],180);self.assertIs(r['timed'],False);self.assertEqual(r['movement'],'static');self.assertEqual(r['autoShuffle'],'free');g=r['generator'];self.assertEqual(g['typeCount'],9);self.assertNotIn('seed',g);screen=[[g['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertEqual(sum(map(sum,screen)),30);self.assertTrue(all(sum(row)==5 for row in screen[3:9]));self.assertTrue(all(sum(row)==0 for row in screen[:3]+screen[9:]))
