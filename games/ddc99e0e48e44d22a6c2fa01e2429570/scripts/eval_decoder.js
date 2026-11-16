const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

// The array function is at the end: from arr3f3aIdx to the end of the file.
const arr3f3aIdx = jsCode.indexOf('function _0x3f3a()');
const fn3797Idx = jsCode.indexOf('function _0x3797');
const fn3797End = jsCode.indexOf('var ParticleManager =');

// Let's get the IIFE at the top
const iifeEnd = jsCode.indexOf('var src = {');

const combined = `
${jsCode.slice(arr3f3aIdx)}
${jsCode.slice(fn3797Idx, fn3797End)}
${jsCode.slice(0, iifeEnd)}
global._0x3797 = _0x3797;
`;

eval(combined);

console.log("0x45c:", _0x3797(0x45c));
console.log("0xda:", _0x3797(0xda));
console.log("0x3bd:", _0x3797(0x3bd));
console.log("0x4ca:", _0x3797(0x4ca));
console.log("0x3aa:", _0x3797(0x3aa));

// In bitamps:
console.log("tut_01_screen_design:", _0x3797(0x3bd));
console.log("tut_02_screen_design:", _0x3797(0x4ca));
console.log("tut_03_screen_design:", _0x3797(0xda));
console.log("tut_04_screen_design:", _0x3797(0x45c));

// Now inspect rules usages around 444100
// switch (_0x21f9d2) {
//   case 0: rules.texture = PIXI.utils.TextureCache[...]
console.log("0x304:", _0x3797(0x304));
console.log("0x299:", _0x3797(0x299));
console.log("0x300:", _0x3797(0x300));
console.log("0x35e:", _0x3797(0x35e));
console.log("0x39b:", _0x3797(0x39b));
console.log("0x256:", _0x3797(0x256));
console.log("0x335:", _0x3797(0x335));
console.log("0x283:", _0x3797(0x283));
