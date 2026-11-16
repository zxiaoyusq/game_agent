const fs = require('fs');
const path = require('path');

const refDir = path.resolve('/root/dev/game-agent/game_agent/ref'); // or relative
console.log("Ref exists check:");
['../ref', '../../ref', '../../../ref', '/root/dev/game-agent/game_agent/ref'].forEach(p => {
  if (fs.existsSync(p)) {
    console.log("Found ref at:", p);
    try {
      const files = fs.readdirSync(p);
      console.log("Files:", files);
    } catch (e) {
      console.log("Error reading:", e.message);
    }
  }
});
