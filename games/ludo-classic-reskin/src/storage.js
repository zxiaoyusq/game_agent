import { uint32, ALGORITHM } from "./rng.js";
import {
  ownersFor,
  pieceCount,
  cellId,
  SAFE,
  legalMoves,
  homeCount,
  targetCount,
} from "./rules.js";
export const MATCH_KEY = "ludo-classic-reskin:match:v1";
export const SETTINGS_KEY = "ludo-classic-reskin:settings:v1";
const integer = (n) => Number.isSafeInteger(n) && n >= 0;
function assert(value, message) {
  if (!value) throw new Error(message);
}
export function validateState(s) {
  assert(
    s && s.version === 1 && s.rulesVersion === "ludo-classic-reskin-1",
    "存档版本不支持",
  );
  assert(
    typeof s.matchId === "string" &&
      s.matchId.length > 0 &&
      s.matchId.length < 100 &&
      integer(s.revision),
    "对局标识无效",
  );
  assert(
    ["classic", "quick"].includes(s.mode) && Array.isArray(s.seats),
    "模式无效",
  );
  // 先验证席位，再按模式检查唯一编号和枚数；坐标只从规则语义推导。
  const owners = ownersFor(s.seats.length);
  assert(
    owners &&
      s.seats.every(
        (v, i) => v.owner === owners[i] && ["human", "ai"].includes(v.type),
      ) &&
      s.seats.some((v) => v.type === "human"),
    "席位无效",
  );
  assert(owners.includes(s.currentPlayer), "当前玩家无效");
  assert(
    Array.isArray(s.pieces) &&
      s.pieces.length === owners.length * pieceCount(s.mode),
    "棋子数量无效",
  );
  const ids = new Set();
  const cells = new Map();
  for (const p of s.pieces) {
    assert(
      owners.includes(p.owner) &&
        Array.from(
          { length: pieceCount(s.mode) },
          (_, i) => `${p.owner}:${i + 1}`,
        ).includes(p.id) &&
        !ids.has(p.id),
      "棋子编号无效",
    );
    ids.add(p.id);
    assert(
      Number.isInteger(p.progress) && p.progress >= -1 && p.progress <= 56,
      "棋子位置无效",
    );
    const cell = cellId(p.owner, p.progress);
    if (cell !== null && cell < 52 && !SAFE.includes(cell)) {
      assert(!cells.has(cell) || cells.get(cell) === p.owner, "普通格异色共存");
      cells.set(cell, p.owner);
    }
  }
  assert(
    s.rng &&
      s.rng.algorithm === ALGORITHM &&
      uint32(s.rng.initialSeed) &&
      uint32(s.rng.state) &&
      integer(s.rng.rawDrawCount),
    "随机存档无效",
  );
  assert(
    s.stats &&
      ["rollCount", "moveCount", "bonusCount", "captureCount"].every((k) =>
        integer(s.stats[k]),
      ) &&
      s.stats.moveCount <= s.stats.rollCount &&
      s.stats.bonusCount <= s.stats.moveCount &&
      s.stats.captureCount <= s.stats.moveCount * s.pieces.length,
    "统计无效",
  );
  assert(
    integer(s.sixStreak) &&
      s.sixStreak <= 2 &&
      ["awaitRoll", "awaitMove", "finished"].includes(s.phase),
    "回合无效",
  );
  if (s.phase === "awaitMove")
    assert(
      Number.isInteger(s.dice) &&
        s.dice >= 1 &&
        s.dice <= 6 &&
        legalMoves(s).length > 0 &&
        (s.dice === 6 ? s.sixStreak >= 1 : s.sixStreak === 0),
      "骰子或合法动作无效",
    );
  else assert(s.dice === null, "未掷骰阶段带有骰子");
  const winning = owners.filter((o) => homeCount(s, o) >= targetCount(s));
  if (s.phase === "finished")
    assert(
      winning.length === 1 && winning[0] === s.winner && s.sixStreak === 0,
      "胜者无效",
    );
  else assert(s.winner === null && winning.length === 0, "未结算却已有胜者");
  // 摘要只是已提交结果；分开校验公共字段与动作字段，不能作为待执行指令。
  if (s.lastEvent !== null) {
    const lastEvent = s.lastEvent;
    const validDice =
      Number.isInteger(lastEvent.dice) &&
      lastEvent.dice >= 1 &&
      lastEvent.dice <= 6;
    const validCaptures =
      Array.isArray(lastEvent.capturedIds) &&
      lastEvent.capturedIds.every((id) => ids.has(id));
    const validBonuses =
      Array.isArray(lastEvent.bonusReasons) &&
      new Set(lastEvent.bonusReasons).size === lastEvent.bonusReasons.length &&
      lastEvent.bonusReasons.every((reason) =>
        ["six", "capture", "home"].includes(reason),
      );
    assert(
      ["ROLL", "MOVE"].includes(lastEvent.type) &&
        owners.includes(lastEvent.actor),
      "事件动作或玩家无效",
    );
    assert(validDice && validCaptures && validBonuses, "事件骰子或奖励无效");
    assert(
      [null, "tripleSix", "noMove"].includes(lastEvent.skipReason),
      "事件跳过原因无效",
    );
    if (lastEvent.type === "MOVE") {
      assert(ids.has(lastEvent.pieceId), "事件棋子无效");
      assert(
        Number.isInteger(lastEvent.from) && lastEvent.from >= -1,
        "事件起点无效",
      );
      assert(
        Number.isInteger(lastEvent.to) &&
          lastEvent.to >= 0 &&
          lastEvent.to <= 56,
        "事件终点无效",
      );
    } else {
      assert(
        lastEvent.pieceId === null &&
          lastEvent.from === null &&
          lastEvent.to === null,
        "掷骰摘要含移动字段",
      );
    }
  }
  return s;
}
export function loadMatch(io) {
  try {
    const text = io.getItem(MATCH_KEY);
    return {
      state: text ? validateState(JSON.parse(text)) : null,
      error: null,
    };
  } catch (e) {
    return { state: null, error: `无法恢复：${e.message}` };
  }
}
export class SaveStore {
  constructor(io) {
    this.io = io;
    this.error = null;
    this.lastText = null;
  }
  // 写失败保持常驻error；只有真正写入成功或用户成功清理才清除。
  save(state) {
    try {
      const text = JSON.stringify(validateState(state));
      this.io.setItem(MATCH_KEY, text);
      this.lastText = text;
      this.error = null;
      return true;
    } catch (e) {
      this.error = "进度未保存，刷新可能丢失";
      return false;
    }
  }
  clear() {
    try {
      this.io.removeItem(MATCH_KEY);
      this.error = null;
      return true;
    } catch (e) {
      this.error = "无法清理存档，请允许浏览器存储";
      return false;
    }
  }
}
