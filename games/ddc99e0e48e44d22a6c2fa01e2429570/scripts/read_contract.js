const fs = require('fs');
const content = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/9db204ec443225710201c78f335ba84fd181be5146d5147a281813de22f74b4a/tutorial-contract.md', 'utf8');
console.log("=== tutorial-contract.md ===");
console.log(content);
