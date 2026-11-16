(function(root){
    'use strict';
    root.CrazyKnifesQualityController=function(){
        var tiers=[1,1.25,1.5],tier=2,requested=2,nextChange=0,start=0;
        var count=0,late=0,render=0,update=0,badWindows=0,goodWindows=0,changes=[];
        function clear(now){start=now;count=late=render=update=0;}
        return {
            observe:function(s){
                if(!s.active){clear(s.now);badWindows=goodWindows=0;return;}
                if(!start)start=s.now;
                count++;if(s.interval>25)late++;render+=s.render;update+=s.update;
                if(s.now-start<2000||count<20)return;
                var slow=late/count>=.2&&render/count>=3&&update<=render*1.25;
                var fast=late/count<.02;
                if(slow){badWindows++;goodWindows=0;}else if(fast){goodWindows++;badWindows=0;if(requested<tier)requested=tier;}else{badWindows=goodWindows=0;requested=tier;}
                if(s.now>=nextChange){
                    if(badWindows>=2&&tier>0)requested=tier-1;
                    else if(goodWindows>=5&&tier<tiers.length-1)requested=tier+1;
                }
                clear(s.now);
            },
            commit:function(now,stable){
                if(!stable||tier===requested||now<nextChange)return false;
                tier=requested;nextChange=now+15000;badWindows=goodWindows=0;
                changes.push({time:now,dpr:tiers[tier]});if(changes.length>16)changes.shift();return true;
            },
            dpr:function(){return tiers[tier];},
            reset:function(now){clear(now);badWindows=goodWindows=0;requested=tier;},
            diagnostics:function(){return {dpr:tiers[tier],requestedDpr:tiers[requested],changes:changes.slice()};}
        };
    };
})(typeof window!=='undefined'?window:globalThis);
