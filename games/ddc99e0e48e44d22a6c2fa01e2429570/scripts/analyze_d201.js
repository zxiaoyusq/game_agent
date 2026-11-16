const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

console.log("Length of jsCode:", jsCode.length);

// Look for tutorial, tut_05, screen_design, freestyle, etc.
const keywords = ['tut_05', 'tutorial', 'screen_design', 'puck', 'Freestyle', 'freestyle', 'rules', 'A potted red'];

keywords.forEach(kw => {
  let idx = 0;
  let count = 0;
  while ((idx = jsCode.indexOf(kw, idx)) !== -1) {
    count++;
    console.log(`Match for '${kw}' at offset ${idx}:`);
    console.log("  Context:", jsCode.slice(Math.max(0, idx - 80), Math.min(jsCode.length, idx + 80)));
    idx += kw.length;
    if (count > 5) {
      console.log(`  ... and more matches for '${kw}'`);
      break;
    }
  }
  if (count === 0) {
    console.log(`No direct match for '${kw}'`);
  }
});
