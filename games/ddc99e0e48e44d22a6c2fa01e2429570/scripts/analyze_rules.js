const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

// Check around offset 444263 and 444695
console.log("=== rules context 1 ===");
console.log(jsCode.slice(444100, 445200));

console.log("=== tut_05 usages ===");
let pos = 0;
while ((pos = jsCode.indexOf('tut_05', pos)) !== -1) {
  console.log(`pos ${pos}:`, jsCode.slice(Math.max(0, pos - 150), Math.min(jsCode.length, pos + 150)));
  pos += 'tut_05'.length;
}
