import { readFile, writeFile } from 'node:fs/promises';
let code = await readFile('scripts/browser-lifecycle.mjs', 'utf8');
code = code.replace("const point=kind==='dice'?{x:rect.x+rect.width/2,y:rect.y+rect.height*.84}:\n        {x:rect.x+(submitted.animation.positions[0].x)*rect.width/360,y:rect.y+submitted.animation.positions[0].y*rect.height/600};\n      for(let i=0;i<10;i++) await page.mouse.click(point.x,point.y);", `const diceBox=await page.locator(\`#dice-\${before.state.currentPlayer}\`).boundingBox();
      const pieceBox=await page.locator('#piece-1').boundingBox();
      assert(diceBox && pieceBox);
      const center=box=>({x:box.x+box.width/2,y:box.y+box.height/2});
      const targets=[center(diceBox),center(pieceBox)];
      const point={x:rect.x+rect.width/2,y:rect.y+rect.height/2};
      for(let i=0;i<10;i++) await page.mouse.click(targets[i%2].x,targets[i%2].y);`);
code = code.replace("assert.equal((await snapshot(page)).state.revision,submitted.state.revision);\n      if(operation", `assert.deepEqual((await snapshot(page)).state,submitted.state);
      let interrupt=await snapshot(page);
      let naturalRetries=0;
      // 若调度错过窗口，从菜单重新自然准备；不把已结束演出当成中断。
      while(!interrupt.busy || interrupt.animation?.kind!==kind) {
        assert(naturalRetries++<2,'重复输入后未命中动画窗口');
        await start(page,'quick',4,'human',seed); await reduced(page,true);
        for(let budget=0;budget<2000;budget++) {
          const o=await snapshot(page),s=o.state,m=chooseMove(s);
          if(kind==='dice'?s.phase==='awaitRoll':s.phase==='awaitMove'&&(kind==='capture'?m.capturedIds.length>0:m.from>=0&&m.to-m.from>=3&&!m.capturedIds.length)) break;
          await input(page,o);await stable(page);assert(budget<1999);
        }
        await reduced(page,false);before=await snapshot(page);await input(page,before);
        await page.waitForFunction(kind=>window.ludo.observe().busy&&window.ludo.observe().animation?.kind===kind,kind);
        submitted=await snapshot(page);interrupt=submitted;
      }
      assert(interrupt.busy);assert.equal(interrupt.animation.kind,kind);
      if(operation`);
code = code.replace('const before=await snapshot(page);', 'let before=await snapshot(page);').replace('const submitted=await snapshot(page);', 'let submitted=await snapshot(page);');
code = code.replace("await page.reload(); await page.locator('#resume').click();", "await page.reload(); await page.waitForFunction(()=>window.ludo?.observe().ready); await page.locator('#resume').click();");
code = code.replace('results.push({kind,operation,before:', 'results.push({kind,operation,clicks:10,targets,naturalRetries,interrupt:{busy:interrupt.busy,kind:interrupt.animation.kind,elapsed:interrupt.animation.elapsed},before:');
code = code.replace("await background.bringToFront();\n    await foreground.waitForFunction(()=>document.hidden);", "const interrupt=await snapshot(foreground);\n    assert(interrupt.busy);assert.equal(interrupt.animation.kind,kind);\n    await background.bringToFront();\n    await foreground.waitForFunction(()=>document.hidden);");
code = code.replace('results.push({kind,visibility:', 'results.push({kind,interrupt:{busy:interrupt.busy,kind:interrupt.animation.kind,elapsed:interrupt.animation.elapsed},visibility:');
const marker = "  await foreground.bringToFront();\n  await start(foreground,'quick',2,'ai',seed);";
const tail = `  await foreground.bringToFront();
  await start(foreground,'quick',2,'ai',1);
  await reduced(foreground,false);
  // 正常动画结束后450ms AI等待提供切后台窗口；必须明确到达AI回合。
  let ai;
  for(let i=0;i<50;i++) {
    const o=await snapshot(foreground);
    const isAi=o.state.seats.find(s=>s.owner===o.state.currentPlayer).type==='ai';
    if(isAi&&!o.busy) {ai=o;break;}
    if(!isAi&&!o.busy) await input(foreground,o);
    await stable(foreground);
  }
  assert(ai,'未自然到达AI回合');
  assert.equal(ai.state.seats.find(s=>s.owner===ai.state.currentPlayer).type,'ai');
  await background.bringToFront();await foreground.waitForFunction(()=>document.hidden);
  const before=await snapshot(foreground);
  assert.deepEqual(before.state,ai.state,'错过AI等待窗口');
  await new Promise(r=>setTimeout(r,2200));
  const hidden=await snapshot(foreground);
  assert.deepEqual(hidden.state,before.state);
  assert(hidden.visibility.some(e=>e.hidden&&e.isTrusted));
  await foreground.bringToFront();await foreground.waitForFunction(()=>!document.hidden);
  await foreground.waitForFunction(revision=>window.ludo.observe().state.revision>revision,before.state.revision);
  const resumed=await snapshot(foreground);
  assert.equal(resumed.state.lastEvent.actor,before.state.currentPlayer);
  results.push({kind:'ai',owner:before.state.currentPlayer,revision:before.state.revision,resumedRevision:resumed.state.revision,visibility:resumed.visibility});
  return results;
}
`;
if (!code.includes(marker)) throw Error('生命周期标记缺失');
code = code.slice(0, code.indexOf(marker)) + tail;
await writeFile('scripts/browser-lifecycle.mjs', code);
console.log('生命周期有限补正已写入');
