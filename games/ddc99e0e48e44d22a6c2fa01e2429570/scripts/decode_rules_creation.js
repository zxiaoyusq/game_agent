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

// Let's decode 438000 to 444000
const chunk = jsCode.slice(438000, 444000);
// Find where rules property is assigned:
const rIdx = chunk.indexOf('rules');
console.log("rIdx:", rIdx);
console.log(chunk.slice(Math.max(0, rIdx - 200), Math.min(chunk.length, rIdx + 400)));

// Let's find all occurrences of "rules" in chunk
let p = 0;
while ((p = chunk.indexOf('rules', p)) !== -1) {
  console.log(`Pos ${p}:`, chunk.slice(Math.max(0, p - 100), Math.min(chunk.length, p + 100)));
  p += 5;
}
