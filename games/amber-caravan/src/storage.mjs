import { validateGame } from './rules.mjs';

export const SAVE_KEY = 'amber-caravan:v1';
const defaultSettings = { sound: true, fast: false };

/** 存档只能恢复经过规则验证的状态；损坏存档不会覆盖新局或阻塞开始。 */
export function loadSave(storage) {
  try {
    // 浏览器可能连 localStorage 属性访问都拒绝，必须在 try 内取得存储对象。
    const target = storage ?? globalThis.localStorage;
    const raw = target.getItem(SAVE_KEY);
    if (!raw) return { game: null, settings: { ...defaultSettings } };
    const data = JSON.parse(raw);
    if (data.version !== 1) throw new Error('版本不支持');
    if (data.game !== null && !validateGame(data.game)) throw new Error('局面不合法');
    return {
      game: data.game || null,
      settings: { sound: data.settings?.sound !== false, fast: data.settings?.fast === true },
    };
  } catch {
    return { game: null, settings: { ...defaultSettings }, warning: '无法读取上次旅程。你仍可以开始新局。' };
  }
}

/** 返回写入结果，由界面持续显示失败状态；不得假称已保存。 */
export function saveGame(game, settings, storage) {
  try {
    if (game !== null && !validateGame(game)) return false;
    const target = storage ?? globalThis.localStorage;
    target.setItem(SAVE_KEY, JSON.stringify({ version: 1, game, settings }));
    return true;
  } catch { return false; }
}
