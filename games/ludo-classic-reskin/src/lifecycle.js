// 取消异步任务之外仍验证令牌，防止已进入队列的旧AI回调污染新局。
export class TaskGate {
  constructor(clock = globalThis) {
    this.clock = clock;
    this.token = 0;
    this.timer = null;
  }
  cancel() {
    this.token++;
    if (this.timer !== null) this.clock.clearTimeout(this.timer);
    this.timer = null;
  }
  schedule(state, delay, isCurrent, callback) {
    this.cancel();
    const token = this.token;
    const { matchId, revision, phase } = state;
    this.timer = this.clock.setTimeout(() => {
      this.timer = null;
      if (token === this.token && isCurrent({ matchId, revision, phase }))
        callback();
    }, delay);
  }
}
