from pathlib import Path
p=Path('tests/browser-host.cjs');s=p.read_text(encoding='utf-8-sig');s=s.replace("await p.screenshot({path:'screenshots/dev_return.png'});await p.mouse.click", "await p.screenshot({path:'screenshots/dev_return.png'});assert.equal(await p.evaluate(()=>cr_getC2Runtime().running_layout.name),'menu');await p.mouse.click")
s=s.replace("await p.screenshot({path:'screenshots/dev_restart.png'});assert.deepEqual(errors,[]);", "await p.screenshot({path:'screenshots/dev_restart.png'});assert.equal(await p.evaluate(()=>cr_getC2Runtime().running_layout.name),'game');assert.equal(await p.evaluate(()=>cr_getC2Runtime().types.t5.instances.length),72);assert.deepEqual(errors,[]);")
p.write_text(s,encoding='utf8')
