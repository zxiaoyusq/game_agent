const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('game/menu-progress.js', 'utf8');

function render(width, height) {
  const label = { style: {} };
  const tile = { x: width / 2, y: height / 2, layer: { layerToCanvas: (x, y, horizontal) => horizontal ? x : y } };
  const runtime = { canvas: { width, height, getBoundingClientRect: () => ({ left: 0, top: 0, width, height }) }, types: { t25: { instances: [tile] } }, running_layout: { name: 'menu' } };
  let frame;
  const context = { document: { createElement: () => label, body: { appendChild() {} } }, requestAnimationFrame: fn => { frame = fn; }, window: { oneConnectProgress: { get: () => 15 }, cr_getC2Runtime: () => runtime } };
  vm.runInNewContext(source, context);
  frame();
  return label;
}

const portrait = render(920, 1854);
assert.ok(Math.abs(parseFloat(portrait.style.width) - 359) < 2);
assert.ok(Math.abs(parseFloat(portrait.style.height) - 97) < 2);
assert.equal(portrait.textContent, 'LEVEL 15');
const landscape = render(1280, 720);
assert.ok(parseFloat(landscape.style.width) < 150);
assert.ok(parseFloat(landscape.style.height) > 35);
assert.ok(Math.abs(parseFloat(landscape.style.left) - 640) < 1);
console.log('menu progress proportions: ok');
