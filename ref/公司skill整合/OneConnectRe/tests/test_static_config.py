import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
class StaticConfig(unittest.TestCase):
 def test_static_and_invalid(self):
  spec=importlib.util.spec_from_file_location('levels',Path('tools/compile_levels.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);src=json.loads(Path('baseline/data.js').read_text(encoding='utf8'))
  m.compile_data(src,{'levels':[{'level':2,'seconds':180,'movement':'static'}]})
  for value in ('fall_down','',False,1):
   with self.assertRaises(ValueError):m.compile_data(src,{'levels':[{'level':2,'seconds':180,'movement':value}]})
 def test_cli_uses_configured_mode(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'levels.json';p.write_text(json.dumps({'levels':[{'level':2,'seconds':180,'movement':'static','board':[[1,1],[2,2]]}]}),encoding='utf8')
   data=json.loads(subprocess.check_output([sys.executable,'tools/board_solver.py',str(p),'--mode','original','--summary'],encoding='utf8'));self.assertEqual(data[0]['mode'],'static')
