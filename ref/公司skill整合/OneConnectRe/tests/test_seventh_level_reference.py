import json,unittest
from pathlib import Path
class SeventhLevelReference(unittest.TestCase):
 def test_level_seven(self):
  r=next((x for x in json.loads(Path('config/levels.json').read_text(encoding='utf8'))['levels'] if x['level']==7),None);self.assertIsNotNone(r,'level 7 must be configured');self.assertEqual(r['seconds'],223);self.assertEqual(r['movement'],'gravity_right');self.assertEqual(r['gravity'],{'top':2,'left':1,'rows':8,'cols':5});self.assertEqual(r['generator']['typeCount'],9);self.assertNotIn('seed',r['generator']);screen=[[r['generator']['mask'][x][11-y] for x in range(6)] for y in range(12)];self.assertTrue(all(sum(row)==5 for row in screen[2:10]));self.assertEqual(sum(map(sum,screen)),40)
