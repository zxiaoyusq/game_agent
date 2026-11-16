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

// Find where "rules" string appears that was used in PIXI code
// We saw _0x1b55a0(0x35e) resolved to "rules" before
// Let's search for "rules" in the decoded context
// But wait, "rules" is not a string literal in the code?
// It was matched as a key in object
console.log("Looking for key 'rules'...");
let p = 0;
while ((p = jsCode.indexOf('rules', p)) !== -1) {
    if (jsCode[p-1] === '"' && jsCode[p+5] === '"') {
        console.log(`Key "rules" at ${p}`);
        console.log(jsCode.slice(p - 100, p + 100));
    }
    p += 5;
}
