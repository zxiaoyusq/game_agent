import importlib.util,json,unittest,copy
from pathlib import Path
class GeneratorConfig(unittest.TestCase):
 def test_generator_valid_and_invalid(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));mask=[[int(y>=1 and 3<=x<=8) for x in range(12)] for y in range(6)];row={'level':2,'seconds':180,'movement':'static','generator':{'mask':mask,'typeCount':9,'seed':42}};m.compile_data(src,{'levels':[row]})
  for mutation in (lambda r:r.update(movement=''),lambda r:r.update(board=[[0]*12 for _ in range(6)]),lambda r:r['generator'].update(typeCount=16),lambda r:r['generator'].update(seed=-1),lambda r:r['generator']['mask'][1].__setitem__(3,0),lambda r:r['generator'].update(unknown=1)):
   q=copy.deepcopy(row);mutation(q)
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[q]})
