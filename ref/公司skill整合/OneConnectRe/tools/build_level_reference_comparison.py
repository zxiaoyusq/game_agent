"""Build a static comparison without importing unverified competitor rules."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'E:\codex_apk_work\竞品拆解\tile connect\07_程序与配置拆解\corrected_reference\level_layout_L1-13_CORRECTED.json')
OUTPUT = ROOT / '关卡竞品配置对照.html'

def build():
    reference = json.loads(SOURCE.read_text(encoding='utf-8'))
    current = json.loads((ROOT / 'config' / 'levels.json').read_text(encoding='utf-8'))
    rows = []
    for level in range(1, 14):
        ref = reference[str(level)]
        w, h, cells = ref['screen_cols'], ref['screen_rows'], ref['datas']
        if not isinstance(w, int) or not isinstance(h, int) or len(cells) != w*h or any(v not in (0,1,2,3) for v in cells):
            raise ValueError(f'Invalid reference matrix for level {level}')
        entry = next((e for e in current['levels'] if e['level'] == level), None)
        rows.append({'level': level, 'cols': w, 'rows': h, 'cells': cells,
                     'shape': ref['shape_id'], 'cfg': ref['cfg'], 'current': entry})
    data = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>关卡配置对照</title><style>body{margin:0;background:#101a32;color:#edf4ff;font:16px system-ui}main{max-width:1100px;margin:auto;padding:24px}.note,.panel{background:#1c2943;padding:18px;border-radius:12px;margin:16px 0}.note{border-left:4px solid #ffd66f}a{color:#9fddff}.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.grid{display:grid;gap:3px;width:max-content;max-width:100%}.cell{width:22px;height:22px;border-radius:4px;background:#79b7e7;text-align:center;font-size:13px;color:#102039}.hole{background:#27344a}.special{background:#ffca58}select{font-size:16px;padding:6px}p{line-height:1.55}.muted{color:#bacbe5}</style>
<main><h1>竞品原始配置与本项目关卡对照</h1><p><a href="关卡可视化总览.html">返回关卡总览</a> · <a id="edit" href="关卡编辑.html">编辑本项目关卡</a></p><div class="note">左侧是 DSH 从竞品文件提取的原始形状配置，按代码确定的屏幕坐标排列；特殊格的运行含义、初始实际牌数及与动态生成的关系尚待确认。右侧是本项目当前配置。两者差异不自动判定为错误，也不会自动覆盖本项目。</div>
<label>关卡 <select id="select"></select></label><div class="cols"><section class="panel"><h2>竞品原始形状配置</h2><p id="refInfo"></p><div id="ref" class="grid"></div><p class="muted">蓝色：普通槽位；深色：洞；黄色：特殊标记 2/3。矩阵并非实机截图。</p><p id="refCfg"></p></section><section class="panel"><h2>本项目当前配置</h2><p id="ownInfo"></p><div id="own" class="grid"></div><p class="muted">蓝色：固定棋子或可用槽位；深色：空格。只展示配置，不代表随机生成出的牌面。</p><p id="ownCfg"></p></section></div><p class="muted">来源：DSH《布局矩阵更正记录.md》与 level_layout_L1-13_CORRECTED.json；本项目 config/levels.json。首关参考形状与教程手写盘可能不同。</p></main>
<script>const data=DATA;const $=id=>document.getElementById(id);let sel=$('select');data.forEach(r=>{let o=document.createElement('option');o.value=r.level;o.textContent='第 '+r.level+' 关';sel.append(o)});function draw(id,m){let el=$(id);el.replaceChildren();if(!m.length){el.textContent='无独立棋盘配置';return}el.style.gridTemplateColumns=`repeat(${m[0].length},22px)`;m.forEach(row=>row.forEach(v=>{let c=document.createElement('div');c.className='cell '+(v===1?'hole':v>1?'special':'');if(v>1)c.textContent=v;el.append(c)}))}function render(){let r=data.find(v=>v.level==sel.value),e=r.current;$('edit').href='关卡编辑.html#level='+r.level;$('refInfo').textContent=`形状 ${r.shape} · ${r.rows} 行 × ${r.cols} 列`;$('refCfg').textContent=`时间 ${r.cfg.time} 秒；方向 上/下/左/右：${r.cfg.up}/${r.cfg.down}/${r.cfg.left}/${r.cfg.right}；boom=${r.cfg.boom}、movenum=${r.cfg.movenum}、repeat=${r.cfg.repeat}（字段含义未全部确认）。`;draw('ref',Array.from({length:r.rows},(_,y)=>r.cells.slice(y*r.cols,(y+1)*r.cols)));let m=e&&(e.board||e.generator?.mask),d=e?.boardSize||{rows:6,cols:12};let ok=Array.isArray(m)&&m.length===d.rows&&m.every(a=>Array.isArray(a)&&a.length===d.cols);let screen=ok?Array.from({length:d.cols},(_,y)=>Array.from({length:d.rows},(_,x)=>m[x][d.cols-1-y]?0:1)):[];draw('own',screen);$('ownInfo').textContent=e?`${d.cols} 行 × ${d.rows} 列 · ${e.board?'固定盘':'生成盘'}`:'本关回退原版规则';$('ownCfg').textContent=e?`时间 ${e.seconds??'原版'} 秒；位移 ${e.movement||'原版规则'}。`:''}sel.onchange=render;render();</script></html>'''
    OUTPUT.write_text(html.replace('DATA', data), encoding='utf-8', newline='\n')
    print(f'{OUTPUT}: {len(rows)} levels')

if __name__ == '__main__':
    build()
