const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

// Extract _0x3f3a array and _0x3797 function and the IIFE
const iifeEnd = jsCode.indexOf('var src = {');
const codePart1 = jsCode.slice(0, iifeEnd);

const fn3797Idx = jsCode.indexOf('function _0x3797');
const arr3f3aIdx = jsCode.indexOf('function _0x3f3a');

console.log("arr3f3aIdx:", arr3f3aIdx);
console.log("fn3797Idx:", fn3797Idx);

// Let's create an environment to evaluate strings
const sandbox = {};
const scriptCode = `
${jsCode.slice(arr3f3aIdx)}
${jsCode.slice(fn3797Idx, arr3f3aIdx)}
${codePart1}
sandbox._0x3797 = _0x3797;
`;

try {
  eval(scriptCode);
  console.log("Decoder initialized successfully!");
  console.log("0x45c:", _0x3797(0x45c));
  console.log("0xda:", _0x3797(0xda));
  console.log("0x3bd:", _0x3797(0x3bd));
  console.log("0x4ca:", _0x3797(0x4ca));
  console.log("0x3aa:", _0x3797(0x3aa));

  // Check lines around 444100
  console.log("0x283:", _0x3797(0x283));
  console.log("0x335:", _0x3797(0x335));
  console.log("0x304:", _0x3797(0x304));
  console.log("0x299:", _0x3797(0x299));
  console.log("0x300:", _0x3797(0x300));
  console.log("0x35e:", _0x3797(0x35e));
  console.log("0x39b:", _0x3797(0x39b));
  console.log("0x256:", _0x3797(0x256));
  console.log("0x333:", _0x3797(0x333));
  console.log("0x491:", _0x3797(0x491));
  console.log("0x151:", _0x3797(0x151));
  console.log("0x4b4:", _0x3797(0x4b4));
  console.log("0x156:", _0x3797(0x156));
  console.log("0x13b:", _0x3797(0x13b));
  console.log("0x197:", _0x3797(0x197));
} catch (e) {
  console.log("Eval error:", e);
}
