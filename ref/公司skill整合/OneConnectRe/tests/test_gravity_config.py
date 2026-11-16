import importlib.util,json,unittest
from pathlib import Path
class GravityConfig(unittest.TestCase):
 def test_gravity_generator_validation(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'));mask=[[0]*12 for _ in range(6)];shape=['001100','011110','111111','111111','011110','001100']
  for y,line in enumerate(shape):
   for x,v in enumerate(line):mask[x][8-y]=int(v)
  base={'level':6,'seconds':163,'movement':'gravity_down','gravity':{'top':3,'left':0,'rows':6,'cols':6},'generator':{'mask':mask,'typeCount':9,'seed':42}}
  m.compile_data(src,{'levels':[base]})
  for bad in ({**base,'gravity':{'top':8,'left':0,'rows':6,'cols':6}},{**base,'movement':'static'},{**base,'gravity':{'top':3,'left':0,'rows':6,'cols':5}},{k:v for k,v in base.items() if k!='gravity'}):
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[bad]})
