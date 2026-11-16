from pathlib import Path
p=Path('开发预览.html');s=p.read_text(encoding='utf8');s=s.replace('<button id="save">下载本次事件</button>','<button id="save">下载本次事件</button><label>广告模拟 <select id="admode"><option value="unavailable">不可用</option><option value="returned">接口返回</option><option value="error">接口报错</option><option value="rejected">异步失败</option></select></label>')
s=s.replace("let records=[],last=0;const frame=", "const mode=document.getElementById('admode');function setMock(){if(mode.value==='unavailable'){delete window.h5_sdk;return}window.h5_sdk={showGameLoadingCompleted(){},showAd(kind){if(mode.value==='error')throw Error('模拟广告错误');if(mode.value==='rejected')return Promise.reject(Error('模拟异步失败'));return {simulated:true,kind}}}}mode.onchange=setMock;setMock();let records=[],last=0;const frame=")
s=s.replace('广告 unavailable 表示没有真实广告服务。','广告模式仅模拟接口行为，不代表真实展示、关闭回调或奖励发放。')
p.write_text(s,encoding='utf8')
