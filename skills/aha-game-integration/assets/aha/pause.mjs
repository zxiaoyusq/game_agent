/** 每个来源使用独立键；广告结束不能解除用户暂停、切后台或宿主弹窗。 */
export function createPauseController({ pause, resume }) {
  const reasons = new Set();
  return {
    set(reason, blocked) {
      const wasPaused = reasons.size > 0;
      if (blocked) reasons.add(reason);
      else reasons.delete(reason);
      if (!wasPaused && reasons.size) pause();
      else if (wasPaused && !reasons.size) resume();
    },
    get paused() { return reasons.size > 0; },
  };
}
