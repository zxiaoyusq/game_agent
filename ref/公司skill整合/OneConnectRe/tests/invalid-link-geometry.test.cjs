const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),m={exports:{}};
vm.runInNewContext(fs.readFileSync('tools/invalid_link_geometry.js','utf8'),{module:m,Number,Array,Math});const middle=m.exports.middleSegment;
let p=middle([{x:0,y:0},{x:10,y:0},{x:10,y:30},{x:20,y:30}]);assert.equal(p.x,10);assert.equal(p.y,15);
p=middle([{x:0,y:0},{x:4,y:0},{x:4,y:6}]);assert.equal(p.x,2);assert.equal(p.y,0);
assert.equal(middle([{x:0,y:0}]),null);assert.equal(middle([{x:0,y:0},{x:NaN,y:0}]),null);
console.log('invalid-link cross uses middle path segment PASS');
