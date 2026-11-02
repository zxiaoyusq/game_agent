"""Compile generated Java and exercise nested copying, markers and CLI contracts.

These are desktop tests with minimal Android API stubs, not Android acceptance.
"""
from pathlib import Path
import subprocess, tempfile, unittest, sys, shutil

GENERATOR = Path(__file__).resolve().parents[1] / 'generate_seed_copier.py'
if '--generator' in sys.argv:
    pos = sys.argv.index('--generator')
    GENERATOR = Path(sys.argv[pos + 1])
    del sys.argv[pos:pos + 2]

STUBS = {
    'android/content/Context.java': '''package android.content;
public class Context {
  private final android.content.res.AssetManager assets; private final java.io.File files;
  public Context(java.io.File a, java.io.File f) { assets=new android.content.res.AssetManager(a); files=f; }
  public Context getApplicationContext() { return this; }
  public android.content.res.AssetManager getAssets() { return assets; }
  public java.io.File getFilesDir() { return files; }
}''',
    'android/content/res/AssetManager.java': '''package android.content.res;
public class AssetManager {
  public static final int ACCESS_STREAMING=2; private final java.io.File base;
  public AssetManager(java.io.File b) { base=b; }
  public String[] list(String p) throws java.io.IOException {
    if (p.equals(System.getProperty("failPath"))) throw new java.io.IOException("injected failure");
    java.io.File f=new java.io.File(base,p);
    String[] names=f.list(); return names==null ? new String[0] : names;
  }
  public java.io.InputStream open(String p) throws java.io.IOException { return open(p,2); }
  public java.io.InputStream open(String p,int mode) throws java.io.IOException {
    return new java.io.FileInputStream(new java.io.File(base,p));
  }
}''',
    'android/util/Log.java': '''package android.util;
public class Log {
  public static int i(String t,String m) { return 0; }
  public static int w(String t,String m) { return 0; }
  public static int w(String t,String m,Throwable e) { return 0; }
  public static int e(String t,String m,Throwable e) { return 0; }
}''',
    'android/os/Looper.java': '''package android.os;
public class Looper { public static Looper getMainLooper() { return new Looper(); } }''',
    'android/os/Handler.java': '''package android.os;
public class Handler {
  public Handler(Looper l) {} public boolean post(Runnable r) { r.run(); return true; }
}''',
}

class SeedCopierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='seed-copier-test-')
        self.root = Path(self.tmp.name)
        self.assets = self.root / 'assets'
        self.files = self.root / 'files'
        self.files.mkdir()
        (self.assets/'remote_seed/patch/nested').mkdir(parents=True)
        (self.assets/'remote_seed/patch/nested/data.bin').write_bytes(b'\x00seed\xff\n')
        (self.assets/'remote_seed/patch/empty.bin').write_bytes(b'')
    def tearDown(self):
        self.tmp.cleanup()
    def generate(self, *args):
        return subprocess.run([sys.executable, '-B', str(GENERATOR), '--package', 'com.demo',
                               '--asset-dir', 'assets/remote_seed', '--out', str(self.root/'SeedCopier.java'),
                               *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    def compile_and_run(self, *args, fail_path=None, entry='copyIfNeeded'):
        proc = self.generate(*args)
        self.assertEqual(proc.returncode,0,proc.stderr)
        for name,text in STUBS.items():
            p=self.root/name; p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
        java = shutil.which('javac')
        if not java:
            self.skipTest('JDK javac unavailable; generated Java runtime not verified')
        runtime = str(Path(java).with_name('java.exe' if sys.platform=='win32' else 'java'))
        call = ('com.demo.SeedCopier.copyIfNeeded(c);' if entry=='copyIfNeeded'
                else 'new com.demo.SeedCopier(c).copySync();')
        (self.root/'Runner.java').write_text('''public class Runner {
          public static void main(String[] a) {
            android.content.Context c=new android.content.Context(new java.io.File(a[0]),new java.io.File(a[1]));
            %s
          }
        }''' % call,encoding='utf-8')
        classes=self.root/'classes'; classes.mkdir(exist_ok=True)
        compile_result=subprocess.run([java,'-encoding','UTF-8','-d',str(classes),
                                       *[str(p) for p in self.root.rglob('*.java')]],capture_output=True,text=True,encoding='utf-8',errors='replace')
        self.assertEqual(compile_result.returncode,0,compile_result.stderr)
        command=[runtime]
        if fail_path:command.append('-DfailPath='+fail_path)
        command += ['-cp',str(classes),'Runner',str(self.assets),str(self.files)]
        run=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        return command
    def test_nested_bytes_empty_file_and_idempotent_marker(self):
        cmd=self.compile_and_run()
        dest=self.files/'seed/patch/nested/data.bin'
        self.assertTrue(dest.is_file(), 'nested leaf must be a file, not file/file')
        self.assertEqual(dest.read_bytes(),b'\x00seed\xff\n')
        self.assertEqual((self.files/'seed/patch/empty.bin').read_bytes(),b'')
        self.assertTrue((self.files/'seed/.seed_done').is_file())
        (self.assets/'remote_seed/patch/nested/data.bin').write_bytes(b'changed')
        again=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(again.returncode,0,again.stderr)
        self.assertEqual(dest.read_bytes(),b'\x00seed\xff\n')
    def test_selected_roots_and_files_dir_layout(self):
        self.compile_and_run('--roots','patch','--target-subdir','.',entry='copySync')
        self.assertEqual((self.files/'patch/nested/data.bin').read_bytes(),b'\x00seed\xff\n')
        self.assertTrue((self.files/'.seed_done').is_file())
    def test_failed_copy_does_not_commit_marker(self):
        self.compile_and_run(fail_path='remote_seed/patch/nested')
        self.assertFalse((self.files/'seed/.seed_done').exists())
    def test_check_does_not_write(self):
        proc=self.generate('--check','--class-name','BootSeed','--java-package','com.custom.seed')
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertFalse((self.root/'SeedCopier.java').exists())
    def test_usage_and_custom_class(self):
        usage=self.root/'usage.md'
        proc=self.generate('--class-name','BootSeed','--java-package','com.custom.seed','--emit-usage',str(usage))
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('class BootSeed',(self.root/'SeedCopier.java').read_text(encoding='utf-8'))
        self.assertIn('com/custom/seed/BootSeed',usage.read_text(encoding='utf-8'))
    def test_traversal_rejected(self):
        proc=self.generate('--target-subdir','../escape')
        self.assertNotEqual(proc.returncode,0)
        self.assertFalse((self.root/'SeedCopier.java').exists())
    def test_java_keywords_rejected(self):
        for value in ('for','try','float','boolean','abstract','class','record','_'):
            with self.subTest(value=value):
                proc=self.generate('--class-name',value,'--check')
                self.assertNotEqual(proc.returncode,0)
        proc=self.generate('--java-package','com.for.seed','--check')
        self.assertNotEqual(proc.returncode,0)
    def test_windows_asset_separators(self):
        self.compile_and_run('--asset-dir','assets\\remote_seed')
        self.assertEqual((self.files/'seed/patch/nested/data.bin').read_bytes(),b'\x00seed\xff\n')
    def test_smali_is_marked_incomplete(self):
        proc=self.generate('--language','smali')
        self.assertEqual(proc.returncode,0,proc.stderr)
        text=(self.root/'SeedCopier.java').read_text(encoding='utf-8')
        self.assertIn('INCOMPLETE',text)
        self.assertIn('TODO',text)

if __name__=='__main__':
    unittest.main()
