(function () {
    'use strict';
    var app, index, boot, active = 0, bound = false;
    var loading = Object.create(null), pending = 0;
    var warmed = new Set(), backgroundStarted=false, poolsPrepared=false,renderEnabled=false,firstReadyAt=0;
    var quality=new CrazyKnifesQualityController(),renderedFrames=0,nextRenderAt=0,lastRenderAt=0;
    var componentData=Object.create(null),componentRequests=Object.create(null),restored=new Set();
    var counters = { assetLoads:0, transitions:0, failures:0, warmups:0 };
    function save() {
        try { return JSON.parse(localStorage.getItem('CrazyKnifes_Save') || '{}') || {}; } catch (_) { return {}; }
    }
    function snapshotBoot() {
        var s=save(),level=Number(s.CrazyKnifes_SavecurrLevel)||0;
        var skin=Number(s.CrazyKnifes_SavechosenSkinId)||0;
        if(level>=3&&!s.CrazyKnifes_Saveskin1)skin=1;
        return {level:level,skin:Math.max(0,Math.min(index.boot.knives.length-1,skin)),environment:Number(s.CrazyKnifes_SaveenvType)||1};
    }
    function unique(ids) { return Array.from(new Set(ids.map(String))); }
    function expand(ids) {
        var out=new Set();
        function add(id){id=String(id);if(out.has(id))return;out.add(id);(index.dependencies[id]||[]).forEach(add);}
        ids.forEach(add);return Array.from(out);
    }
    function ready(ids) { return ids.every(function(id){var a=app.assets.get(Number(id));return a&&a.loaded&&a.resource!==null;}); }
    function asset(id) {
        id=String(id);var a=app.assets.get(Number(id));
        if(!a)return Promise.reject(new Error('Unknown asset '+id));
        if(a.loaded&&a.resource!==null)return Promise.resolve();
        if(loading[id])return loading[id];
        loading[id]=new Promise(function(resolve,reject){
            function clean(){a.off('load',done);a.off('error',fail);}
            function done(){clean();resolve();}
            function fail(error){clean();reject(new Error(a.name+': '+error));}
            a.once('load',done);a.once('error',fail);counters.assetLoads++;app.assets.load(a);
        }).finally(function(){delete loading[id];});
        return loading[id];
    }
    function ensure(ids) { return Promise.all(expand(ids).map(asset)); }
    function loadComponents(key){
        if(componentData[key])return Promise.resolve(componentData[key]);
        if(componentRequests[key])return componentRequests[key];
        var entry=index.boot.componentFiles[key];if(!entry)return Promise.reject(new Error('Unknown component bundle '+key));
        componentRequests[key]=fetch(entry.url+'?v='+window.CC_CACHE_VERSION).then(function(r){if(!r.ok)throw new Error(entry.url+': HTTP '+r.status);return r.json();}).then(function(data){
            if(data.root!==entry.root||Object.keys(data.components||{}).length!==entry.records)throw new Error('Incomplete component bundle '+key);
            componentData[key]=data;return data;
        }).finally(function(){delete componentRequests[key];});return componentRequests[key];
    }
    function decode(value){
        if(Array.isArray(value))return value.map(decode);if(!value||typeof value!=='object')return value;
        var out={},fields=index.compressedFormat.fieldArray;
        Object.keys(value).forEach(function(key){var n=0;for(var i=0;i<key.length;i++)n=n*95+key.charCodeAt(i)-32;out[typeof fields[n]==='string'?fields[n]:key]=decode(value[key]);});return out;
    }
    function restoreComponents(key){
        if(restored.has(key))return;
        var data=componentData[key];if(!data)throw new Error('Components not prepared '+key);
        var root=app.root.findByGuid(data.root);if(!root)throw new Error('Missing deferred root '+key);
        var records=Object.keys(data.components).map(function(id){var entity=app.root.findByGuid(id);if(!entity)throw new Error('Missing deferred node '+id);return {entity:entity,components:decode(data.components[id])};});
        var preloading=app.systems.script.preloading;app.systems.script.preloading=true;
        try{
            app.systems.list.forEach(function(system){records.forEach(function(record){var c=record.components[system.id];if(c&&!record.entity.c[system.id])system.addComponent(record.entity,c);});});
        }finally{app.systems.script.preloading=preloading;}
        app.systems.fire('initialize',root);app.systems.fire('postInitialize',root);app.systems.fire('postPostInitialize',root);
        restored.add(key);
    }
    function idsForGame(game) {
        var ids=Game.bonusLevel?Game.bonusIds:Game.levelIds;
        var assets=index.boot.common.concat(index.boot.knives[game.chosenSkinId]||[]);
        var envs=[Game.bonusLevel?6:game.envType];
        if(!Game.bonusLevel&&game.envTypeSameCount>=4)envs=[1,3,4,5];
        envs.forEach(function(t){assets=assets.concat(index.boot.environments[t]||[]);});
        ids.forEach(function(id){if(!index.levels[id])throw new Error('Unknown level '+id);assets=assets.concat(index.levels[id].assets);});
        return {levels:ids.slice(),assets:unique(assets),components:['knife-'+game.chosenSkinId]};
    }
    function isPrepared(state){return state.levels.every(CrazyKnifesLevels.ready)&&ready(state.assets)&&(state.components||[]).every(function(key){return !!componentData[key];});}
    function overlay(show,error) {
        var e=document.getElementById('cc-resource-status');
        if(!e){e=document.createElement('div');e.id='cc-resource-status';e.style.cssText='position:fixed;inset:0;z-index:10000003;display:none;align-items:center;justify-content:center;background:#142331;pointer-events:auto';e.innerHTML='<div style="width:28px;height:28px;border:4px solid #ffffff55;border-top-color:#fff;border-radius:50%;animation:cc-spin .8s linear infinite"></div>';var style=document.createElement('style');style.textContent='@keyframes cc-spin{to{transform:rotate(360deg)}}';document.head.appendChild(style);document.body.appendChild(e);}
        e.style.display=show?'flex':'none';
        if(error){e.textContent='↻';e.style.fontSize='48px';e.onclick=function(){location.reload();};}
    }
    function run(game,state,commit) {
        if(isPrepared(state))return commit();
        var token=++active;pending++;counters.transitions++;
        var previousControls=game.controlsEnabled,previousInput=Input.mouseDis,previousPaused=game.paused;
        game.controlsEnabled=false;Input.mouseDis=true;Input.mouseDown=false;
        if(Input.flushPresses)Input.flushPresses();
        game.paused=true;
        overlay(true);
        return Promise.all([CrazyKnifesLevels.ensure(state.levels),ensure(state.assets),Promise.all((state.components||[]).map(loadComponents))]).then(function(){
            if(token!==active)return;
            game.controlsEnabled=previousControls;Input.mouseDis=previousInput;game.paused=previousPaused;
            if(game.addedLevelsCount>0)overlay(false);
            return commit();
        }).catch(function(error){counters.failures++;console.error('[Crazy Knifes resources]',error);overlay(true,true);throw error;}).finally(function(){pending--;});
    }
    function prepareView(game) {
        if(!poolsPrepared){
            [['Trail1',12],['Trail2',12],['EffectDrop',8],['Effect3DDrop',6],['MsgText',4]].forEach(function(item){
                var pool=ObjectPool.pool[item[0]];if(!pool)return;
                var limit=Math.min(item[1],pool.maxCount);
                while(pool.pool.length<limit)ObjectPool.push(pool.entity.clone());
            });poolsPrepared=true;
        }
        var seen=new Set(),targets=[];
        game.levelObjectsE.findComponents('script').filter(function(c){return c.sliceable;}).sort(function(a,b){return a.entity.getPosition().x-b.entity.getPosition().x;}).some(function(c){
            var type=c.entity.name,key=Environment.instance.type+'|'+game.chosenSkinId+'|'+type;
            if(seen.has(type))return false;seen.add(type);
            if(!warmed.has(key))targets.push({key:key,slice:c.sliceable});
            return seen.size>=3;
        });
        renderEnabled=true;app.autoRender=true;
        if(!targets.length){overlay(false);if(!backgroundStarted){firstReadyAt=performance.now();backgroundStarted=true;background();}return;}
        var layer=app.scene.layers.getLayerById(0),extras=[],warmNode=new pc.GraphNode('Material preparation');
        warmNode.setPosition(Knife.instance.entity.getPosition());warmNode.setLocalScale(.0001,.0001,.0001);
        targets.forEach(function(target){
            [target.slice.left,target.slice.right].forEach(function(entity){if(!entity)return;
                entity.findComponents('model').concat(entity.findComponents('render')).forEach(function(c){
                    (c.meshInstances||[]).forEach(function(source){
                        if(extras.length>=24||!source.mesh||!source.material)return;
                        var mesh=new pc.MeshInstance(source.mesh,source.material,warmNode);
                        mesh.cull=false;mesh.castShadow=false;mesh.receiveShadow=source.receiveShadow;extras.push(mesh);
                    });
                });
            });
        });
        if(!extras.length){overlay(false);if(!backgroundStarted){firstReadyAt=performance.now();backgroundStarted=true;background();}return;}
        var controls=game.controlsEnabled,input=Input.mouseDis,paused=game.paused;
        game.controlsEnabled=false;Input.mouseDis=true;game.paused=true;if(Input.flushPresses)Input.flushPresses();overlay(true);
        layer.addMeshInstances(extras);counters.warmups++;
        return new Promise(function(resolve){
            app.once('postrender',function(){
                layer.removeMeshInstances(extras);extras.forEach(function(mesh){mesh.destroy();});
                targets.forEach(function(target){warmed.add(target.key);});
                app.once('postrender',function(){
                    game.controlsEnabled=controls;Input.mouseDis=input;game.paused=paused;overlay(false);
                    if(!backgroundStarted){firstReadyAt=performance.now();backgroundStarted=true;background();}resolve();
                });
            });
        });
    }
    function bindGame() {
        if(bound)return;bound=true;
        Game.prototype.prepareLevel.call({currLevel:boot.level},false);
        boot.levels=Game.levelIds.slice();boot.previous=Game.levelIdsPrev.slice();
        CrazyKnifesLevels.ensure(boot.levels).catch(function(error){console.warn('[Crazy Knifes prefetch]',String(error));});
        ensure([].concat.apply([],boot.levels.map(function(id){return index.levels[id].assets;}))).catch(function(error){console.warn('[Crazy Knifes prefetch]',String(error));});
        var restart=Game.prototype.restart;
        Game.prototype.restart=function(){var game=this,args=arguments,state=idsForGame(game);return run(game,state,function(){restoreComponents('knife-'+game.chosenSkinId);var result=restart.apply(game,args);var view=prepareView(game);return Promise.resolve(view).then(function(){window.CrazyKnifesAhaClient.markReady();return result;});});};
        var apply=Game.prototype.applyChosenSkin;
        Game.prototype.applyChosenSkin=function(){var game=this,args=arguments,key='knife-'+game.chosenSkinId;return run(game,{levels:[],assets:index.boot.knives[game.chosenSkinId]||[],components:[key]},function(){restoreComponents(key);return apply.apply(game,args);});};
        var action=Gui.buttonAction;
        Gui.buttonAction=function(name){var args=arguments,owner=this;CrazyKnifesRenderRecovery.wake();if(name!=='shopOpen')return action.apply(owner,args);return run(Game.instance,{levels:[],assets:index.boot.shop,components:['shop']},function(){restoreComponents('shop');return action.apply(owner,args);});};
    }
    function cacheCanvasRect() {
        var device=app.graphicsDevice,update=device.updateClientRect,last=0,dirty=true;
        var invalidate=function(){dirty=true;};
        device.updateClientRect=function(){var now=performance.now();if(dirty||now-last>1000){update.call(device);last=now;dirty=false;}};
        ['resize','orientationchange','scroll'].forEach(function(name){window.addEventListener(name,invalidate,{passive:true,capture:true});});
        var observer=window.ResizeObserver?new ResizeObserver(invalidate):null;if(observer)observer.observe(device.canvas);
        app.once('destroy',function(){if(observer)observer.disconnect();['resize','orientationchange','scroll'].forEach(function(name){window.removeEventListener(name,invalidate,true);});});
    }
    function governFrames(){
        document.addEventListener('visibilitychange',function(){lastRenderAt=nextRenderAt=0;quality.reset(performance.now());});
        app.on('framerender',function(){
            app.autoRender=false;
            if(!renderEnabled||document.hidden){app.renderNextFrame=false;return;}
            var now=performance.now(),period=1000/60;
            if(CrazyKnifesRenderRecovery.forceFrame(now)){app.renderNextFrame=true;nextRenderAt=now+period;}
            else if(now+.5>=nextRenderAt){app.renderNextFrame=true;nextRenderAt=nextRenderAt?nextRenderAt+period:now+period;if(now-nextRenderAt>period)nextRenderAt=now+period;}
            else app.renderNextFrame=false;
        });
        app.on('postrender',function(){
            var now=performance.now(),g=window.Game&&Game.instance,k=window.Knife&&Knife.instance;
            var active=!!g&&!document.hidden&&!g.paused&&!g.hdEnabled&&g.controlsEnabled&&now-firstReadyAt>1500;
            renderedFrames++;
            if(lastRenderAt)quality.observe({now:now,interval:now-lastRenderAt,render:app.stats.frame.renderTime||0,update:app.stats.frame.updateTime||0,active:active});
            lastRenderAt=now;
            quality.commit(now,active&&!Input.mouseDown&&(!k||k.state===0)&&(Game.state===Game.STATE_INTRO||Game.state===Game.STATE_PLAYING));
        });
    }
    function background() {
        var todo=app.assets.list().filter(function(a){return ['model','texture','audio','font','textureatlas','container','template'].indexOf(a.type)>=0&&!a.loaded&&a.file;}).map(function(a){return a.id;});
        function next(){
            if(!todo.length)return;
            var g=window.Game&&Game.instance,k=window.Knife&&Knife.instance;
            if(pending||document.hidden||!g||g.paused||Input.mouseDown||performance.now()-firstReadyAt<1500||Game.state===Game.STATE_PLAYING&&k&&k.state!==0){setTimeout(next,500);return;}
            var id=todo.shift();asset(id).catch(function(error){console.warn('[Crazy Knifes background]',String(error));}).finally(schedule);
        }
        function schedule(){if(window.requestIdleCallback)requestIdleCallback(next,{timeout:2000});else setTimeout(next,80);}
        schedule();
    }
    window.CrazyKnifesPerformance={
        prepareConfiguration:function(config){index=CrazyKnifesLevels.index();boot=snapshotBoot();
            loadComponents('knife-'+boot.skin).catch(function(error){console.warn('[Crazy Knifes component prefetch]',String(error));});
            var ids=unique(index.boot.common.concat(index.boot.knives[boot.skin],index.boot.environments[boot.environment]||index.boot.environments[1]));
            var first=index.boot.firstLevels[boot.level];
            if(first){
                first.forEach(function(id){ids=ids.concat(index.levels[id].assets);});
                CrazyKnifesLevels.ensure(first).catch(function(error){console.warn('[Crazy Knifes prefetch]',String(error));});
            }
            var set=new Set(ids);
            var scripts=new Set((window.SCRIPTS||[]).map(String));
            Object.keys(config.assets).forEach(function(id){config.assets[id].preload=scripts.has(id)||set.has(id);});
            return config;
        },
        configure:function(application){app=application;CrazyKnifesRenderRecovery.attach(app);cacheCanvasRect();governFrames();return boot;},
        bind:bindGame,
        prepareInitialLevel:function(game){
            if(Number(game.currLevel)===boot.level&&boot.levels){Game.bonusLevel=false;Game.levelIds=boot.levels.slice();Game.levelIdsPrev=boot.previous.slice();return;}
            return game.prepareLevel(false);
        },
        prepareScene:function(scene){return loadComponents('knife-'+boot.skin).then(function(bundle){var roots=index.boot.roots,entities=scene.entities;
            scene.compressedFormat=index.compressedFormat;
            Object.keys(bundle.components).forEach(function(id){entities[id]["'"]=bundle.components[id];});restored.add('knife-'+boot.skin);
            roots.knives.forEach(function(id,i){entities[id][' ']=i===boot.skin;});
            roots.grounds.forEach(function(id){entities[id][' ']=false;});
            var selection=index.boot.envSelections[boot.environment]||index.boot.envSelections[1];
            [['environments',1],['backgrounds',2],['lights',3]].forEach(function(pair){roots[pair[0]].forEach(function(id,i){if(id&&entities[id])entities[id][' ']=i===selection[pair[1]];});});
            entities[roots.shop][' ']=false;
            });
        },
        enter:function(game,commit){return run(game,idsForGame(game),commit);},
        startBackground:background,
        qualityDpr:function(){return quality.dpr();}
    };
}());
