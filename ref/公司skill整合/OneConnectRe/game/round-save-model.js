(function () {
  'use strict';
  function canonical(value) {
    if (Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
    if (value && typeof value === 'object') return '{'+Object.keys(value).sort().map(function(k){return JSON.stringify(k)+':'+canonical(value[k]);}).join(',')+'}';
    return JSON.stringify(value);
  }
  function fingerprint(entry) { return canonical(entry); }
  function validate(s,entry) {
    if (!s || !entry || s.version!==1 || !Number.isInteger(s.level) || s.level!==entry.level) return false;
    var sameConfig=s.config===fingerprint(entry);
    if (!sameConfig && (entry.autoShuffle===undefined || entry.autoShuffle==='free' || entry.autoShuffle==='original')) {
      // Only this policy can change without altering the saved board or counters.
      var previous=Object.assign({},entry);delete previous.autoShuffle;
      sameConfig=s.config===fingerprint(previous) || s.config===fingerprint(Object.assign({},previous,{autoShuffle:'free'})) || s.config===fingerprint(Object.assign({},previous,{autoShuffle:'original'}));
    }
    if (!sameConfig) return false;
    var size=entry.boardSize||{rows:6,cols:12};
    if (!Number.isInteger(s.rows)||!Number.isInteger(s.cols)||s.rows!==size.rows||s.cols!==size.cols||s.rows<1||s.cols<1||s.rows>12||s.cols>12) return false;
    if (!Array.isArray(s.board)||s.board.length!==s.rows||s.board.some(function(row){return !Array.isArray(row)||row.length!==s.cols;})) return false;
    var counts={},total=0;
    for (var row of s.board) for (var v of row) { if (!Number.isInteger(v)||v<0||v>30) return false; if(v){counts[v]=(counts[v]||0)+1;total++;} }
    if (total<2 || Object.keys(counts).some(function(k){return counts[k]%2!==0;})) return false;
    var source=entry.board||(entry.generator&&entry.generator.mask);
    if(Array.isArray(source)){
      var maximum=source.reduce(function(n,row){return n+row.filter(Boolean).length;},0);
      if(total>maximum)return false;
    }
    if(['gravity_down','gravity_up','gravity_left','gravity_right'].includes(entry.movement)){
      var g=entry.gravity;
      if(!g||!Number.isInteger(g.top)||!Number.isInteger(g.left)||!Number.isInteger(g.rows)||!Number.isInteger(g.cols))return false;
      for(var y=0;y<s.rows;y++)for(var x=0;x<s.cols;x++)if(s.board[y][x]&&!(g.left<=y&&y<g.left+g.cols&&g.top<=s.cols-1-x&&s.cols-1-x<g.top+g.rows))return false;
    }
    if (!Number.isFinite(s.timer)||s.timer<=0||s.timer>3600 || !Number.isFinite(s.score)||s.score<0 || !Number.isInteger(s.tip)||s.tip<0||s.tip>999 || !Number.isInteger(s.shuffle)||s.shuffle<0||s.shuffle>999) return false;
    return true;
  }
  window.oneConnectRoundSaveModel={fingerprint:fingerprint,validate:validate};
}());
