import json,shutil,sys,tempfile,unittest
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
from build_game_package import create

class PackageLevelConsistency(unittest.TestCase):
 def test_rejects_uncompiled_config_without_mutating_worker_or_writing_zip(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game);out=Path(tmp)/'game.zip'
   config=json.loads((root/'config/levels.json').read_text(encoding='utf8'));config['levels'][0]['seconds']+=1
   expected=Path(tmp)/'levels.json';expected.write_text(json.dumps(config),encoding='utf8');worker=game/'offline-worker.js';before=worker.read_bytes()
   with self.assertRaisesRegex(ValueError,'level configuration mismatch'):create(game,out,expected_config=expected)
   self.assertFalse(out.exists());self.assertEqual(worker.read_bytes(),before)
 def test_rejects_malformed_generated_configuration(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game);(game/'level-config.js').write_text('not valid config',encoding='utf8')
   with self.assertRaisesRegex(ValueError,'invalid generated level configuration'):create(game,Path(tmp)/'game.zip',expected_config=root/'config/levels.json')
 def test_rejects_stale_construct_data_even_if_level_config_matches(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game);out=Path(tmp)/'game.zip'
   data=json.loads((game/'data.js').read_text(encoding='utf8'));data['project'][1]='incorrect-layout'
   (game/'data.js').write_text(json.dumps(data),encoding='utf8');worker=game/'offline-worker.js';before=worker.read_bytes()
   with self.assertRaisesRegex(ValueError,'Construct data mismatch'):create(game,out,expected_config=root/'config/levels.json')
   self.assertFalse(out.exists());self.assertEqual(worker.read_bytes(),before)
 def test_current_compiled_configuration_passes(self):
  with tempfile.TemporaryDirectory() as tmp:
   game=Path(tmp)/'game';shutil.copytree(root/'game',game)
   self.assertGreater(create(game,Path(tmp)/'game.zip',expected_config=root/'config/levels.json')[0],0)

if __name__=='__main__':unittest.main()
