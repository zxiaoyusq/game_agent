import importlib.util,json,shutil,sys,tempfile,unittest,zipfile
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
spec=importlib.util.spec_from_file_location('oc_package',root/'tools/build_game_package.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class EffectPackageIntegrity(unittest.TestCase):
 def test_current_game_packages_original_effects(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game);out=Path(tmp)/'game.zip'
   count,size,digest=module.create(game,out);self.assertGreater(count,0);self.assertGreater(size,0);self.assertEqual(len(digest),64)
   with zipfile.ZipFile(out) as package:
    for name in ('dots-sheet0.png','line-sheet0.png','popfx-sheet0.png','popfx-sheet1.png'):
     self.assertEqual(package.read('images/'+name),(root/'baseline'/'images'/name).read_bytes())

 def test_original_files_present_but_wrong_effect_reference_is_rejected(self):
  for index,replacement in ((7,'images/line-sheet0.png'),(8,'images/dots-sheet0.png'),(48,'images/line-sheet0.png')):
   with self.subTest(index=index),tempfile.TemporaryDirectory() as tmp:
    game=Path(tmp)/'game';shutil.copytree(root/'game',game);(game/'offline-worker.js').unlink()
    data=json.loads((game/'data.js').read_text(encoding='utf8'));data['project'][3][index][7][0][7][0][0]=replacement
    (game/'data.js').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    with self.assertRaisesRegex(ValueError,'original effect definition mismatch'):module.create(game,Path(tmp)/'bad.zip')
    self.assertFalse((Path(tmp)/'bad.zip').exists())

 def test_original_pop_animation_timing_is_protected(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game);(game/'offline-worker.js').unlink()
   data=json.loads((game/'data.js').read_text(encoding='utf8'));data['project'][3][48][7][0][1]+=1
   (game/'data.js').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
   with self.assertRaisesRegex(ValueError,'original effect definition mismatch'):module.create(game,Path(tmp)/'bad.zip')
   self.assertFalse((Path(tmp)/'bad.zip').exists())

 def test_invalid_effect_does_not_rebuild_offline_worker(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game)
   worker=game/'offline-worker.js';before=worker.read_bytes()
   data=json.loads((game/'data.js').read_text(encoding='utf8'));data['project'][3][48][7][0][1]+=1
   (game/'data.js').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
   with self.assertRaisesRegex(ValueError,'original effect definition mismatch'):module.create(game,Path(tmp)/'bad.zip')
   self.assertEqual(worker.read_bytes(),before)

if __name__=='__main__':unittest.main()
