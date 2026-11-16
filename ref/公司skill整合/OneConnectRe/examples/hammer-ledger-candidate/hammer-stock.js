(function(){
 'use strict';
 var key='oneconnect.hammer.v2',legacy='oneconnect.hammer.v1',limit=5000;
 function load(){var raw=localStorage.getItem(key);if(raw===null){var old=localStorage.getItem(legacy),n=old!==null&&/^\d+$/.test(old)?Number(old):2;return {version:2,count:Number.isInteger(n)&&n>=0&&n<=999?n:2,claims:[]};}var v=JSON.parse(raw);if(!v||v.version!==2||!Number.isInteger(v.count)||v.count<0||v.count>999||!Array.isArray(v.claims)||v.claims.length>limit||v.claims.some(function(x){return typeof x!=='string'||!x||x.length>128;}))throw Error('invalid hammer stock');return v;}
 function get(){return load().count;}
 function setCount(n){if(!Number.isInteger(n)||n<0||n>999)return false;try{var v=load();v.count=n;localStorage.setItem(key,JSON.stringify(v));return true;}catch(_){return false;}}
 function has(claim){return load().claims.indexOf(claim)>=0;}
 function grant(claim){if(typeof claim!=='string'||!claim.trim()||claim.length>128)return 'invalid_claim';try{var v=load();if(v.claims.indexOf(claim)>=0)return 'already_claimed';if(v.count>=999||v.claims.length>=limit)return 'full';v.count++;v.claims.push(claim);localStorage.setItem(key,JSON.stringify(v));return 'granted';}catch(_){return 'storage_error';}}
 window.oneConnectHammerStock={get:get,setCount:setCount,has:has,grant:grant};
}());
