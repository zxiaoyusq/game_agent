/* Candidate adapter. Not loaded by the production game until the complete
 * board, tool and tutorial layout has been assembled for user review. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectLayoutAdapter = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  var originals = new Map(), pauseControls = new Set(), anchors = new Map(), hiddenTools = new Map();
  function toolCounter(items, role, uid) {
    return items.find(function(x){return x.instance_vars && x.instance_vars[0]===role;}) ||
      items.find(function(x){return x.uid===uid && (!x.instance_vars || x.instance_vars.length===0 || x.instance_vars[0]===role);});
  }

  // Anchor.tick otherwise moves the native sprite back to its original HUD
  // position after this adapter moves it. Retain and restore its prior state.
  function suspendAnchor(instance) {
    var Anchor = typeof cr !== 'undefined' && cr.behaviors && cr.behaviors.Anchor;
    if (!Anchor || !Anchor.prototype.Instance) return;
    (instance.behavior_insts || []).forEach(function (behavior) {
      if (!(behavior instanceof Anchor.prototype.Instance)) return;
      if (!anchors.has(behavior)) anchors.set(behavior, behavior.enabled);
      behavior.enabled = false;
    });
  }

  // Construct's layerToCanvas/canvasToLayer use CSS pixels on Retina builds
  // and backing-buffer pixels on other builds. getBoundingClientRect is always
  // CSS pixels; convert at this boundary instead of using devicePixelRatio twice.
  function toLayer(runtime, layer, clientX, clientY, rect) {
    rect = rect || runtime.canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) throw new Error('canvas is not visible');
    var ratio = runtime.isRetina ? runtime.devicePixelRatio : 1;
    var x = (clientX - rect.left) * runtime.canvas.width / rect.width / ratio;
    var y = (clientY - rect.top) * runtime.canvas.height / rect.height / ratio;
    return {x: layer.canvasToLayer(x, y, true), y: layer.canvasToLayer(x, y, false)};
  }

  function moveInstance(runtime, instance, x, y, rect) {
    if (!instance || !instance.layer || typeof instance.set_bbox_changed !== 'function') {
      throw new Error('missing Construct UI instance');
    }
    suspendAnchor(instance);
    var pos = toLayer(runtime, instance.layer, x, y, rect);
    if (!originals.has(instance)) originals.set(instance, {x: instance.x, y: instance.y, width: instance.width, height: instance.height});
    if (Math.abs(instance.x - pos.x) < 0.01 && Math.abs(instance.y - pos.y) < 0.01) return;
    instance.x = pos.x;
    instance.y = pos.y;
    instance.set_bbox_changed();
    runtime.redraw = true;
  }

  function fitTool(runtime, instance, slot, rect) {
    var original = originals.get(instance); rect = rect || runtime.canvas.getBoundingClientRect();
    if (!original || !rect.width || !rect.height) return;
    var layer = instance.layer, ratio = runtime.isRetina ? runtime.devicePixelRatio : 1;
    function point(x, y) {
      return {x: layer.layerToCanvas(x, y, true) * ratio * rect.width / runtime.canvas.width,
        y: layer.layerToCanvas(x, y, false) * ratio * rect.height / runtime.canvas.height};
    }
    var center = point(instance.x, instance.y), px = point(instance.x + original.width, instance.y),
      py = point(instance.x, instance.y + original.height);
    var projectedWidth = Math.hypot(px.x - center.x, px.y - center.y),
      projectedHeight = Math.hypot(py.x - center.x, py.y - center.y);
    if (!projectedWidth || !projectedHeight) return;
    var scale = Math.min(1.12, slot.width * 0.64 / projectedWidth, slot.height * 0.84 / projectedHeight);
    var width = original.width * scale, height = original.height * scale;
    if (Math.abs(instance.width - width) < 0.01 && Math.abs(instance.height - height) < 0.01) return;
    instance.width = width; instance.height = height; instance.set_bbox_changed(); runtime.redraw = true;
  }

  function moveHud(runtime, header) {
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return false;
    var all = ['t21','t24','t25','t36'].flatMap(function (name) {
      return runtime.types[name] && runtime.types[name].instances || [];
    });
    function byUid(uid) { return all.find(function (instance) { return instance.uid === uid; }); }
    var groups = [
      {anchor:32, uids:[32,34], x:0.055},
      {anchor:7, uids:[7,8,50], x:0.205},
      {anchor:31, uids:[31,33,51], x:0.49},
      {anchor:26, uids:[26], x:0.935}
    ];
    if (groups.some(function (group) { return !byUid(group.anchor); })) return false;
    var rect = runtime.canvas.getBoundingClientRect(), ratio = runtime.isRetina ? runtime.devicePixelRatio : 1;
    function project(instance, position) {
      var layer = instance.layer;
      return {x: rect.left + layer.layerToCanvas(position.x, position.y, true) * ratio * rect.width / runtime.canvas.width,
        y: rect.top + layer.layerToCanvas(position.x, position.y, false) * ratio * rect.height / runtime.canvas.height};
    }
    groups.forEach(function (group) {
      var anchor = byUid(group.anchor);
      if (!originals.has(anchor)) originals.set(anchor, {x:anchor.x, y:anchor.y, width:anchor.width, height:anchor.height});
      var reference = project(anchor, originals.get(anchor));
      group.uids.forEach(function (uid) {
        var item = byUid(uid);
        if (!item) return;
        if (!originals.has(item)) originals.set(item, {x:item.x, y:item.y, width:item.width, height:item.height});
        var point = project(item, originals.get(item));
        moveInstance(runtime, item, header.left + header.width * group.x + point.x - reference.x,
          header.top + header.height * 0.5 + point.y - reference.y, rect);
      });
    });
    return true;
  }

  // Existing objects, rather than screenshots or overlay images, retain their
  // native touch handling and current tutorial lookups by animation frame.
  function moveTools(runtime, layout) {
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return false;
    var type = runtime.types && runtime.types.t26;
    if (!type || !Array.isArray(type.instances)) return false;
    var slots = Object.fromEntries(layout.tools.map(function (slot) { return [slot.id, slot]; }));
    var counts = runtime.types.t25 && runtime.types.t25.instances || [];
    var controls = [
      {frame: 0, slot: slots.shuffle, countUid: 2, countRole: 3},
      {frame: 1, slot: slots.hint, countUid: 46, countRole: 4}
    ];
    if (controls.some(function (item) {
      return !item.slot || !type.instances.some(function (instance) { return instance.cur_frame === item.frame; });
    })) return false;
    var rect = runtime.canvas.getBoundingClientRect();
    controls.forEach(function (item) {
      var button = type.instances.find(function (instance) { return instance.cur_frame === item.frame; });
      var count = toolCounter(counts, item.countRole, item.countUid);
      var slot = item.slot;
      moveInstance(runtime, button, slot.left + slot.width * 0.38, slot.top + slot.height * 0.5, rect);
      fitTool(runtime, button, slot, rect);
      if (count) moveInstance(runtime, count, slot.left + slot.width * 0.73, slot.top + slot.height * 0.5, rect);
    });
    return true;
  }

  function setToolsHidden(runtime, hidden) {
    var buttons = runtime.types.t26 && runtime.types.t26.instances || [];
    var counts = runtime.types.t25 && runtime.types.t25.instances || [];
    var targets = buttons.filter(function(item) { return item.cur_frame === 0 || item.cur_frame === 1; })
      .concat([toolCounter(counts,3,2),toolCounter(counts,4,46)].filter(Boolean));
    if (hidden) targets.forEach(function(item) {
      if (!hiddenTools.has(item)) hiddenTools.set(item, item.visible);
      if (item.visible) { item.visible = false; runtime.redraw = true; }
    });
    else {
      hiddenTools.forEach(function(visible, item) {
        if (targets.indexOf(item) >= 0 && item.visible !== visible) { item.visible = visible; runtime.redraw = true; }
      });
      hiddenTools.clear();
    }
  }

  // Reposition the native pause controls only after all expected objects exist.
  // Their Construct events, animation frames and visibility remain the owner.
  function movePause(runtime) {
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return false;
    var buttons = runtime.types.t22 && runtime.types.t22.instances || [];
    var sound = runtime.types.t23 && runtime.types.t23.instances || [];
    // Pausing creates new objects each time. Do not retain destroyed controls
    // in the restoration map for the rest of a long-running level.
    pauseControls.forEach(function (item) {
      if (buttons.indexOf(item) < 0 && sound.indexOf(item) < 0) {
        originals.delete(item);
        pauseControls.delete(item);
      }
    });
    var pause = runtime.all_global_vars && runtime.all_global_vars.find(function (v) { return v.name === 'pause'; });
    if (!pause || !pause.data) return false;
    var ordered = [0, 1, 2].map(function (frame) {
      return buttons.find(function (item) { return item.cur_frame === frame; });
    });
    if (ordered.some(function (item) { return !item || !item.visible; }) || sound.length !== 1 || !sound[0].visible) return false;
    var rect = runtime.canvas.getBoundingClientRect();
    if (!rect.width || !rect.height || rect.width >= rect.height) return false;
    var positions = [0.36, 0.46, 0.56, 0.66];
    ordered.concat(sound[0]).forEach(function (item, i) {
      pauseControls.add(item);
      var slot = {left:rect.left + rect.width * 0.25, top:rect.top + rect.height * (positions[i] - 0.04),
        width:rect.width * 0.5, height:rect.height * 0.08};
      moveInstance(runtime, item, rect.left + rect.width * 0.5, rect.top + rect.height * positions[i], rect);
      fitTool(runtime, item, slot, rect);
    });
    return true;
  }

  function restore(runtime) {
    if (runtime && runtime.types) setToolsHidden(runtime, false);
    originals.forEach(function (position, instance) {
      if (instance && instance.runtime === runtime && typeof instance.set_bbox_changed === 'function') {
        instance.x = position.x;
        instance.y = position.y;
        instance.width = position.width;
        instance.height = position.height;
        instance.set_bbox_changed();
      }
    });
    if (runtime && originals.size) runtime.redraw = true;
    originals.clear();
    anchors.forEach(function (enabled, behavior) { behavior.enabled = enabled; });
    anchors.clear();
    pauseControls.clear();
  }

  return {toLayer: toLayer, moveInstance: moveInstance, moveTools: moveTools, setToolsHidden:setToolsHidden, moveHud: moveHud, movePause: movePause, restore: restore};
});
