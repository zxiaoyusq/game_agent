const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

// Find string array and decode function
// Usually at the beginning or end
console.log("=== First 500 chars ===");
console.log(jsCode.slice(0, 500));

// Let's search where _0x14d186 is defined or used (around 444000)
console.log("=== Around 443000 - 444500 ===");
console.log(jsCode.slice(443000, 444200));
