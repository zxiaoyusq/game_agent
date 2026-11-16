const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const files = [
  'mcp-inputs/mac-codex/945f81aa5e020112e0ffcbbbf3953fd1ce5a0e0666373b1a2cc4b0ee2de6b096/tutorial-original.webp',
  'mcp-inputs/mac-codex/6a6b35b973a41ed46d23cc7a5faf6460722f6a019f032f420dbea0252a3869eb/tutorial-mockup.png',
  'mcp-inputs/mac-codex/9db204ec443225710201c78f335ba84fd181be5146d5147a281813de22f74b4a/tutorial-contract.md',
  'mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js'
];

const baseRef = '/root/dev/game-agent/game_agent/ref';

files.forEach(f => {
  const full = path.join(baseRef, f);
  if (fs.existsSync(full)) {
    const stat = fs.statSync(full);
    const buf = fs.readFileSync(full);
    const hash = crypto.createHash('sha256').update(buf).digest('hex');
    console.log(`FILE: ${f}`);
    console.log(`  Size: ${stat.size} bytes`);
    console.log(`  SHA256: ${hash}`);
    if (f.endsWith('.webp') || f.endsWith('.png')) {
      console.log(`  Header (hex): ${buf.slice(0, 32).toString('hex')}`);
      console.log(`  Header (ascii): ${buf.slice(0, 32).toString('ascii').replace(/[^\x20-\x7E]/g, '.')}`);
      if (buf.slice(0, 4).toString('ascii') === 'RIFF' && buf.slice(8, 12).toString('ascii') === 'WEBP') {
        // Parse WebP VP8X chunk if present
        if (buf.slice(12, 16).toString('ascii') === 'VP8X') {
          const width = 1 + buf.readUIntLE(24, 3);
          const height = 1 + buf.readUIntLE(27, 3);
          console.log(`  WebP VP8X Dimensions: ${width} x ${height}`);
        }
      } else if (buf.slice(0, 8).toString('hex') === '89504e470d0a1a0a') {
        // PNG header
        const width = buf.readUInt32BE(16);
        const height = buf.readUInt32BE(20);
        console.log(`  PNG Dimensions: ${width} x ${height}`);
      }
    }
  } else {
    console.log(`NOT FOUND: ${full}`);
  }
});
