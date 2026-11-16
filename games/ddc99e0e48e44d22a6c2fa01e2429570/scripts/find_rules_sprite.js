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

// Check around 440000 - 446000 (Rules dialog definition and layout)
console.log("=== Dialog rules class dissection ===");
// Find where "rules" is created as a Sprite / Container
let idx = jsCode.indexOf('"rules"');
while (idx !== -1) {
  console.log(`Match "rules" at ${idx}:`);
  console.log(jsCode.slice(idx - 100, idx + 200));
  idx = jsCode.indexOf('"rules"', idx + 1);
}
