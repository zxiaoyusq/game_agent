from pathlib import Path
import json
b2=[[x//2+1 for x in range(12)] for y in range(6)];b3=[[(x//2+7) for x in range(12)] for y in range(6)]
Path('config/board-validation.json').write_text(json.dumps({'levels':[{'level':1,'seconds':300},{'level':2,'seconds':180,'board':b2},{'level':3,'seconds':180,'board':b3}]},ensure_ascii=False),encoding='utf8')
s=Path('tests/natural-three.cjs').read_text(encoding='utf8');s=s.replace("for(let i=0;i<120;i++){let s=await state();", "let checked=new Set();for(let i=0;i<120;i++){let s=await state();if((s.level===2||s.level===3)&&!checked.has(s.level)&&s.tiles.length===72){for(let t of s.tiles){let col=Math.round((t.x-89)/101);let expected=Math.floor(col/2)+(s.level===2?0:6);if(t.frame!==expected)throw Error('configured board mismatch level '+s.level+' col '+col+' frame '+t.frame)}checked.add(s.level);console.log('VERIFIED_BOARD',s.level);}")
s=s.replace("console.log('FINAL',", "if(!checked.has(2)||!checked.has(3))throw Error('board checks incomplete');console.log('FINAL',")
s=s.replace("screenshots/config_level3.png", "screenshots/board_level3.png")
Path('tests/natural-board-progress.cjs').write_text(s,encoding='utf8')
