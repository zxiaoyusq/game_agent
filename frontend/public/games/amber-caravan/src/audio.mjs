/** 用少量振荡器合成轻柔的木质、金属反馈，不下载音频或依赖外部服务。 */
export function createAudio() {
  let context;
  let enabled = true;
  function unlock() {
    if (!enabled) return;
    try {
      context ??= new (window.AudioContext || window.webkitAudioContext)();
      if (context.state === 'suspended') context.resume().catch(() => {});
    } catch { /* 浏览器禁用音频时，玩法仍正常继续。 */ }
  }
  function play(type) {
    if (!enabled || !context || context.state !== 'running') return;
    const notes = { roll: [180, 240, 320], move: [440, 660], capture: [330, 494, 659], home: [523, 659, 784], win: [392, 523, 659, 784, 1047] }[type] || [440];
    for (let index = 0; index < notes.length; index++) {
      const start = context.currentTime + index * .075;
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = type === 'roll' ? 'triangle' : 'sine';
      oscillator.frequency.setValueAtTime(notes[index], start);
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(.08, start + .009);
      gain.gain.exponentialRampToValueAtTime(.001, start + .23);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(start);
      oscillator.stop(start + .25);
    }
  }
  return { unlock, play, setEnabled(value) { enabled = value; } };
}
