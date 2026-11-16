const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const window={addEventListener(){}};
const context={window,Number,Array,Object};
const dir=process.argv[2];vm.runInNewContext(fs.readFileSync(dir?dir+'/competitor-star-reference.js':'config/competitor_star_reference.js','utf8'),context);
const ref=window.oneConnectCompetitorStarReference;
assert.equal(ref.unit,'competitor fly-star count');
assert.equal(ref.baseVerified,false,'unverified base must not produce or persist ratings');
for(let level=1;level<=500;level++){
  const t=ref.levels[level];assert(Array.isArray(t)&&t.length===3,`missing level ${level}`);
  assert(t.every(Number.isSafeInteger)&&t[0]>0&&t[0]<=t[1]&&t[1]<=t[2],`invalid thresholds at level ${level}`);
}
assert.deepEqual(Array.from(ref.levels[1]),[20,30,40]);
vm.runInNewContext(fs.readFileSync(dir?dir+'/fly-star-score-candidate.js':'tools/fly_star_score_candidate.js','utf8'),context);
const score=window.oneConnectFlyStarScoreCandidate;score.begin(1);assert.equal(score.rating(1),null,'provisional base is not an earned rating');ref.baseVerified=true;assert.equal(score.rating(1).stars,0);
const original=ref.levels[1];ref.levels[1]=[40,30,20];assert.equal(score.rating(1),null,'malformed thresholds must not award stars');ref.levels[1]=original;
console.log('provisional star bases remain gated and invalid ordering rejected PASS');
