import json,unittest
from pathlib import Path
class FirstLevelReference(unittest.TestCase):
 def test_first_level_matches_reference_portrait_layout(self):
  data=json.loads(Path('config/levels.json').read_text(encoding='utf8'));entry=next(x for x in data['levels'] if x['level']==1);self.assertEqual(entry['seconds'],180);b=entry['board'];display=[[b[x][11-y] for x in range(6)] for y in range(12)];actual=[row[1:6] for row in display[4:9]];expected=[[0,5,0,8,3],[0,7,8,2,6],[3,1,0,1,2],[4,5,0,0,7],[6,4,0,0,0]];self.assertEqual(actual,expected);self.assertEqual(sum(v!=0 for row in display for v in row),16)
