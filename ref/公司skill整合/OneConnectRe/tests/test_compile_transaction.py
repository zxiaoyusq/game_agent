import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('oc_compile_levels',ROOT/'tools/compile_levels.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)

class CompileTransactionTests(unittest.TestCase):
    def test_second_replace_failure_restores_both_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'data.js';configout=root/'level-config.js';source=root/'levels.json'
            target.write_bytes(b'old data');configout.write_bytes(b'old config')
            source.write_text(json.dumps({'levels':[{'level':1,'seconds':180}]}),encoding='utf8')
            real_replace=os.replace;count=0
            def fail_second(src,dst):
                nonlocal count
                count+=1
                if count==2: raise OSError('simulated failure')
                return real_replace(src,dst)
            with patch.object(sys,'argv',['compile_levels.py','--config',str(source),'--output',str(target)]), patch.object(compiler.os,'replace',side_effect=fail_second):
                with self.assertRaises(OSError): compiler.main()
            self.assertEqual(target.read_bytes(),b'old data')
            self.assertEqual(configout.read_bytes(),b'old config')

    def test_worker_failure_leaves_all_original_outputs_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'data.js';configout=root/'level-config.js';worker=root/'offline-worker.js';source=root/'levels.json'
            target.write_bytes(b'old data');configout.write_bytes(b'old config');worker.write_bytes(b'old worker')
            (root/'game.html').write_text('game',encoding='utf8')
            source.write_text(json.dumps({'levels':[{'level':1,'seconds':180}]}),encoding='utf8')
            sys.path.insert(0,str(ROOT/'tools'))
            try:
                import build_offline_worker
                with patch.object(sys,'argv',['compile_levels.py','--config',str(source),'--output',str(target)]), patch.object(build_offline_worker,'build',side_effect=OSError('worker failure')):
                    with self.assertRaises(OSError): compiler.main()
            finally:
                sys.path.remove(str(ROOT/'tools'))
            self.assertEqual(target.read_bytes(),b'old data')
            self.assertEqual(configout.read_bytes(),b'old config')
            self.assertEqual(worker.read_bytes(),b'old worker')

    def test_worker_publish_failure_restores_all_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';game.mkdir();target=game/'data.js';configout=game/'level-config.js';worker=game/'offline-worker.js';source=root/'levels.json'
            target.write_bytes(b'old data');configout.write_bytes(b'old config');worker.write_bytes(b'old worker');(game/'game.html').write_text('game',encoding='utf8')
            source.write_text(json.dumps({'levels':[{'level':1,'seconds':180}]}),encoding='utf8')
            real_replace=os.replace
            def fail_worker(src,dst):
                if Path(dst)==worker: raise OSError('worker publish failure')
                return real_replace(src,dst)
            sys.path.insert(0,str(ROOT/'tools'))
            try:
                with patch.object(sys,'argv',['compile_levels.py','--config',str(source),'--output',str(target)]), patch.object(compiler.os,'replace',side_effect=fail_worker):
                    with self.assertRaises(OSError): compiler.main()
            finally: sys.path.remove(str(ROOT/'tools'))
            self.assertEqual([x.read_bytes() for x in (target,configout,worker)],[b'old data',b'old config',b'old worker'])

    def test_successful_worker_manifest_matches_new_outputs(self):
        import hashlib
        import re
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';game.mkdir();target=game/'data.js';configout=game/'level-config.js';worker=game/'offline-worker.js';source=root/'levels.json'
            target.write_bytes(b'old data');configout.write_bytes(b'old config');worker.write_bytes(b'old worker');(game/'game.html').write_text('game',encoding='utf8')
            source.write_text(json.dumps({'levels':[{'level':1,'seconds':180}]}),encoding='utf8')
            sys.path.insert(0,str(ROOT/'tools'))
            try:
                with patch.object(sys,'argv',['compile_levels.py','--config',str(source),'--output',str(target)]): compiler.main()
            finally: sys.path.remove(str(ROOT/'tools'))
            manifest=json.loads(re.search(r'const MANIFEST=(.*);',worker.read_text(encoding='utf8')).group(1))
            for name,file in [('data.js',target),('level-config.js',configout)]:
                self.assertEqual(manifest['./'+name],hashlib.sha256(file.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
