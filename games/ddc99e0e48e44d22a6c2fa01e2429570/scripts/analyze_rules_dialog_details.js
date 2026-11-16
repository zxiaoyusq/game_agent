const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

const arr3f3aIdx = jsCode.indexOf('function _0x3f3a()');
const fn3797Idx = jsCode.indexOf('function _0x3797');
const fn3797End = jsCode.indexOf('var ParticleManager =');
const iifeEnd = jsCode.indexOf('var src = {');

const combined = `
${jsCode.slice(arr3f3aIdx)}
${jsCode.slice(fn3797Idx, fn3797End)}
${jsCode.slice(0, iifeEnd)}
global._0x3797 = _0x3797;
`;
eval(combined);

// Let's decode around 441000 - 444500 where this._items[0].rules is created!
const chunk = jsCode.slice(441500, 444500);
// Replace _0x... calls with decoded strings where possible or print structure
console.log("Chunk length:", chunk.length);

// Let's inspect where _0x14d186 constructor starts
const constructorIdx = jsCode.lastIndexOf('function _0x14d186', 444000);
console.log("constructorIdx:", constructorIdx);
console.log(jsCode.slice(constructorIdx, constructorIdx + 2000));
