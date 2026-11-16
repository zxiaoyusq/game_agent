import importlib.util,json,unittest
from pathlib import Path
root=Path.cwd();path=root/'tools/compile_levels.py';spec=importlib.util.spec_from_file_location('candidate',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MoreGravity(unittest.TestCase):
 def test_up_left_generated_are_valid(self):
  src=json.loads((root/'baseline/data.js').read_text(encoding='utf8'));mask=[[int(1<=y<5 and 5<=x<9) for x in range(12)] for y in range(6)]
  for direction in ('up','left'):
   row={'level':13,'seconds':180,'movement':'gravity_'+direction,'gravity':{'top':3,'left':1,'rows':4,'cols':4},'generator':{'mask':mask,'typeCount':8,'seed':42}}
   m.compile_data(src,{'levels':[row]})
if __name__=='__main__':unittest.main()
