"""Prepare isolated local WebView performance candidates; never alter baseline."""
import json, shutil, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_offline_worker_candidate import build
analysis=root/'analysis'
for src,name in ((root/'baseline','perf_original_20261031'),(root/'game','perf_current_20261031'),(root/'game','perf_control_20261031')):
    target=analysis/name
    shutil.copytree(src,target,dirs_exist_ok=True)
    if name=='perf_original_20261031':
        html=target/'game.html'
        text=html.read_text(encoding='utf8')
        shim="<script>(function(){if(!('serviceWorker' in navigator))return;var timer=setInterval(function(){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();if(!r||!r.running_layout)return;clearInterval(timer);navigator.serviceWorker.register('./offline-worker.js',{scope:'./'});},1000)})();</script>\n"
        if '</body>' not in text: raise RuntimeError('baseline game body missing')
        html.write_text(text.replace('</body>',shim+'</body>',1),encoding='utf8')
    if name=='perf_control_20261031':
        subprocess.run([sys.executable,str(root/'tools/compile_levels.py'),'--config',str(root/'tests/fixtures/perf_72_control.json'),'--output',str(target/'data.js')],cwd=root,check=True)
    else: print(name,*build(target))
