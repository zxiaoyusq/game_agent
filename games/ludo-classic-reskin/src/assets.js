export async function loadAssets() {
  const response = await fetch('./assets/visual-manifest.json');
  if (!response.ok) throw new Error('资源清单加载失败');
  const manifest = await response.json();
  const images = new Map();
  await Promise.all(
    manifest.assets
      .filter((a) => a.output_format === 'PNG')
      .map(async (asset) => {
        const image = new Image();
        image.src = `./${asset.runtime_path}`;
        await image.decode();
        images.set(asset.runtime_path, image);
      }),
  );
  return { manifest, images };
}
// full-canvas 已恢复原画布；trimmed-sprite 只恢复一次原尺寸和偏移。
export function drawSprite(ctx, assets, path, x, y, scale = 1) {
  const spec = assets.manifest.assets.find((a) => a.runtime_path === path);
  const image = assets.images.get(path);
  if (!image || !spec) throw new Error(`缺失纹理：${path}`);
  const [width, height] = spec.originalSize;
  const [w, h] = spec.size;
  const trimmed = spec.draw_mode === 'trimmed-sprite';
  const left = trimmed ? (width - w) / 2 + spec.offset[0] : 0;
  const top = trimmed ? (height - h) / 2 - spec.offset[1] : 0;
  ctx.drawImage(
    image,
    x - (width * scale) / 2 + left * scale,
    y - (height * scale) / 2 + top * scale,
    w * scale,
    h * scale,
  );
}
export function createAudio() {
  const audio = Object.fromEntries(
    ['roll', 'step', 'capture', 'home'].map((kind) => [
      kind,
      new Audio(`./assets/sound-${kind}.mp3`),
    ]),
  );
  let unlocked = false;
  let muted = false;
  return {
    unlock() {
      unlocked = true;
    },
    mute(value) {
      muted = value;
      if (value) this.stop();
    },
    play(kind) {
      if (!unlocked || muted) return;
      const sound = audio[kind];
      sound.pause();
      sound.currentTime = 0;
      sound.play().catch(() => {}); // 音频不可用不阻塞规则与输入。
    },
    stop() {
      Object.values(audio).forEach((sound) => {
        sound.pause();
        sound.currentTime = 0;
      });
    },
  };
}
