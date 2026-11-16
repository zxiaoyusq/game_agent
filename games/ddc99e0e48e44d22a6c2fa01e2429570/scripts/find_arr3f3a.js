const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

const arr3f3aIdx = jsCode.indexOf('function _0x3f3a()');
console.log("arr3f3aIdx:", arr3f3aIdx);
console.log(jsCode.slice(arr3f3aIdx, arr3f3aIdx + 300));
