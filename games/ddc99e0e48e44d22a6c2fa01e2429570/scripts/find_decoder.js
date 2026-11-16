const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

// Let's execute the deobfuscation function to resolve strings
// Find _0x3797 definition and array definition
const fnIdx = jsCode.indexOf('function _0x3797');
const arrIdx = jsCode.indexOf('function _0x1c44'); // or check the array name
console.log("fnIdx:", fnIdx);

// Look around beginning:
console.log(jsCode.slice(0, 1500));
