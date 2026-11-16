/* 存档失败保留内存纪录与持续提示，只有真实写成功才清除。 */
(function(root){
  'use strict';
  const KEY='animal-tetris-best-v1';
  class BestStore {
    constructor(storage){this.storage=storage;this.best=0;this.warning='';
      try{const raw=storage.getItem(KEY);if(raw){const v=JSON.parse(raw);if(v.version===1 && Number.isSafeInteger(v.bestScore)&&v.bestScore>=0)this.best=v.bestScore;else this.warning='最高分记录无效，已忽略';}}
      catch(e){this.warning='最高分暂未保存，仅本次有效';}
    }
    save(score){this.best=Math.max(this.best,score);try{this.storage.setItem(KEY,JSON.stringify({version:1,bestScore:this.best}));this.warning='';return true;}catch(e){this.warning='最高分暂未保存，仅本次有效';return false;}}
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={BestStore,KEY};else root.TetrisStorage={BestStore,KEY};
})(globalThis);
