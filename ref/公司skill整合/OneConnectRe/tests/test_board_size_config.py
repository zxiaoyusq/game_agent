import importlib.util,json,unittest,copy
from pathlib import Path
class BoardSizeConfig(unittest.TestCase):
 def test_verified_8x8_and_rejections(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'))
  mask=[[int(y<4) for x in range(8)] for y in range(8)]
  row={'level':8,'seconds':196,'movement':'static','boardSize':{'rows':8,'cols':8,'itemSize':75,'spacing':5,'offsetX':320,'offsetY':35},'generator':{'mask':mask,'typeCount':15}}
  m.compile_data(src,{'levels':[row]})
  for mutation in (lambda r:r['boardSize'].update(rows=7),lambda r:r['boardSize'].update(offsetX=0),lambda r:r.update(movement='gravity_down'),lambda r:r['generator']['mask'].pop(),lambda r:r['generator']['mask'][0].pop()):
   q=copy.deepcopy(row);mutation(q)
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[q]})
 def test_expanded_gravity_and_rejections(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'))
  lines=['#########','########.','####..#..','#..###..#','######.##','###...###','..#..#..#'];mask=[[0]*10 for _ in range(8)]
  for y,line in enumerate(lines):
   for x,ch in enumerate(line):mask[y][x+1]=int(ch=='#')
  row={'level':13,'seconds':188,'movement':'gravity_down','boardSize':{'rows':8,'cols':10,'itemSize':75,'spacing':5,'offsetX':240,'offsetY':35},'gravity':{'top':0,'left':0,'rows':9,'cols':7},'generator':{'mask':mask,'typeCount':12}}
  m.compile_data(src,{'levels':[row]})
  for mutation in (lambda r:r['gravity'].update(rows=11),lambda r:r['gravity'].update(cols=9),lambda r:r['boardSize'].update(offsetX=320),lambda r:r['generator']['mask'][7].__setitem__(0,1),lambda r:r['generator']['mask'].pop()):
   q=copy.deepcopy(row);mutation(q)
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[q]})
