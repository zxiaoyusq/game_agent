const fs = require('fs');
const jsCode = fs.readFileSync('/root/dev/game-agent/game_agent/ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js', 'utf8');

const arr3f3aIdx = jsCode.indexOf('function _0x3f3a');
const fn3797Idx = jsCode.indexOf('function _0x3797');

const scriptCode = `
${jsCode.slice(arr3f3aIdx, fn3797Idx + 200)}
var _0x3797 = function(_0x18d100, _0x808e76) {
  var _0x3f3a46 = _0x3f3a();
  _0x3797 = function(_0x3797c8, _0x24ef7e) {
    _0x3797c8 = _0x3797c8 - 0xcf;
    var _0x47b8e7 = _0x3f3a46[_0x3797c8];
    return _0x47b8e7;
  };
  return _0x3797(_0x18d100, _0x808e76);
};
`;

try {
  eval(scriptCode);
  console.log("Testing _0x3797:");
  // Let's test some offsets found in tutorial / rules
  // tut_01_screen_design offset hex in code?
  // Let's find tut_01_screen_design in jsCode
  const idx = jsCode.indexOf('tut_01_screen_design');
  console.log("tut_01_screen_design context:", jsCode.slice(idx - 20, idx + 60));
  
  // Let's decode 0x3bd (which was tut_01_screen_design value in some match)
  console.log("0x3bd ->", _0x3797(0x3bd));
  console.log("0x4ca ->", _0x3797(0x4ca));
  console.log("0xda ->", _0x3797(0xda));
  console.log("0x45c ->", _0x3797(0x45c));
  console.log("0x326 ->", _0x3797(0x326));
  console.log("0x329 ->", _0x3797(0x329));
  console.log("0x327 ->", _0x3797(0x327));

  // Let's check rule images or texts around rules
  // Let's search for "rules" or tutorial images
  for (let i = 0xce; i < 0x500; i++) {
    const val = _0x3797(i);
    if (typeof val === 'string' && (val.includes('tutorial') || val.includes('rule') || val.includes('puck'))) {
      console.log(`0x${i.toString(16)} -> ${val}`);
    }
  }
} catch (e) {
  console.log("Error:", e);
}
