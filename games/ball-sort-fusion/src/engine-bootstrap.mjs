import * as cc from '../engine/cc.js';
// 官方引擎独立构建时没有 Creator 的资源导入数据库，因此显式注册相同的 UI Effect/材质。
// Effect 元信息取自该版本官方测试夹具，GLSL 按官方 builtin-graphics/sprite 源码展开。
export async function bootEngine() {
  const effects = await fetch('./assets/effects.json').then(response => response.json());
  cc.game.on(cc.Game.EVENT_POST_SUBSYSTEM_INIT, () => {
    for (const data of effects) {
      const effect = Object.assign(new cc.EffectAsset(), data);
      effect.onLoaded();
    }
    for (const [name, effectName, defines] of [
      ['ui-graphics-material', 'builtin-graphics', {}],
      ['ui-base-material', 'builtin-sprite', { USE_TEXTURE: false }],
      ['ui-sprite-material', 'builtin-sprite', { USE_TEXTURE: true }],
      ['ui-sprite-alpha-sep-material', 'builtin-sprite', { USE_TEXTURE: true }],
    ]) {
      const material = new cc.Material(); material._uuid = name;
      material.initialize({ effectName, defines });
      cc.builtinResMgr.addAsset(name, material);
    }
  });
  await cc.game.init({
    debugMode: cc.DebugMode.WARN,
    overrideSettings: {
      rendering: { renderMode: 0, customPipeline: false },
      screen: { designResolution: { width: 540, height: 960, policy: 4 }, frameRate: 60 },
      splashScreen: { totalTime: 0 },
      profiling: { showFPS: false },
    },
  });
  cc.game.run();
  return cc;
}
