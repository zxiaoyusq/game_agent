import copy, importlib.util, json, unittest
from pathlib import Path

root=Path.cwd()
spec=importlib.util.spec_from_file_location('compiler',root/'tools/compile_levels.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)

class ExpandedGravity(unittest.TestCase):
 def test_all_gravity_directions_compile_and_check_bounds(self):
  src=json.loads((root/'baseline/data.js').read_text(encoding='utf8'))
  entry={'level':16,'seconds':600,'movement':'gravity_up','boardSize':{'rows':8,'cols':12,'itemSize':65,'spacing':5,'offsetX':220,'offsetY':100},'gravity':{'top':0,'left':0,'rows':12,'cols':8},'board':[[x//2+1 for x in range(12)] for _ in range(8)]}
  for direction in ('up','down','left','right'):
   row=copy.deepcopy(entry);row['movement']='gravity_'+direction;compiler.compile_data(src,{'levels':[row]})
  bad=copy.deepcopy(entry);bad['gravity']['cols']=7
  with self.assertRaises(ValueError):compiler.compile_data(src,{'levels':[bad]})

if __name__=='__main__': unittest.main()
