import { createRng, bounded } from "./rng.js";
export const SAFE = Object.freeze([0, 8, 13, 21, 26, 34, 39, 47]);
export const ownersFor = (count) =>
  ({ 2: [0, 2], 3: [0, 1, 2], 4: [0, 1, 2, 3] })[count]?.slice();
export const pieceCount = (mode) => (mode === "classic" ? 4 : 2);
export function cellId(owner, progress) {
  if (progress < 0) return null;
  return progress <= 50
    ? (13 * owner + progress) % 52
    : 52 + 6 * owner + progress - 51;
}
export const homeCount = (state, owner) =>
  state.pieces.filter((p) => p.owner === owner && p.progress === 56).length;
export const targetCount = (state) => (state.mode === "classic" ? 4 : 1);
export function createMatch({ mode = "classic", seats, seed, matchId }) {
  const owners = ownersFor(seats?.length);
  const validMode = ["classic", "quick"].includes(mode);
  const validSeats =
    owners &&
    seats.every(
      (seat, index) =>
        seat.owner === owners[index] && ["human", "ai"].includes(seat.type),
    );
  const hasHuman = seats?.some((seat) => seat.type === "human");
  if (!validMode || !validSeats || !hasHuman) {
    throw new Error("席位设置无效，至少一位真人");
  }
  const first = bounded(createRng(seed), seats.length);
  return {
    version: 1,
    rulesVersion: "ludo-classic-reskin-1",
    matchId,
    revision: 0,
    mode,
    seats: structuredClone(seats),
    pieces: seats.flatMap((s) =>
      Array.from({ length: pieceCount(mode) }, (_, i) => ({
        id: `${s.owner}:${i + 1}`,
        owner: s.owner,
        progress: mode === "quick" && i === 0 ? 0 : -1,
      })),
    ),
    currentPlayer: seats[first.value].owner,
    phase: "awaitRoll",
    dice: null,
    sixStreak: 0,
    rng: first.rng,
    stats: { rollCount: 0, moveCount: 0, bonusCount: 0, captureCount: 0 },
    winner: null,
    lastEvent: null,
  };
}
export function targetProgress(piece, dice) {
  if (!Number.isInteger(dice) || dice < 1 || dice > 6 || piece.progress === 56)
    return null;
  if (piece.progress === -1) return dice === 6 ? 0 : null;
  return piece.progress + dice <= 56 ? piece.progress + dice : null;
}
export function legalMoves(state) {
  if (state.phase !== "awaitMove") return [];
  return state.pieces
    .filter((p) => p.owner === state.currentPlayer)
    .flatMap((p) => {
      const to = targetProgress(p, state.dice);
      if (to === null) return [];
      const cell = cellId(p.owner, to);
      const capturedIds =
        cell < 52 && !SAFE.includes(cell)
          ? state.pieces
              .filter(
                (q) =>
                  q.owner !== p.owner &&
                  q.progress >= 0 &&
                  q.progress <= 50 &&
                  cellId(q.owner, q.progress) === cell,
              )
              .map((q) => q.id)
          : [];
      return [
        {
          pieceId: p.id,
          from: p.progress,
          to,
          cell,
          capturedIds,
          safe: cell >= 52 || SAFE.includes(cell),
        },
      ];
    });
}
export function bonusReasons(six, capture, home, win = false) {
  return win
    ? []
    : [six && "six", capture && "capture", home && "home"].filter(Boolean);
}
function nextPlayer(state) {
  const index = state.seats.findIndex((s) => s.owner === state.currentPlayer);
  state.currentPlayer = state.seats[(index + 1) % state.seats.length].owner;
  state.sixStreak = 0;
}
const event = (type, actor, dice) => ({
  type,
  actor,
  dice,
  pieceId: null,
  from: null,
  to: null,
  capturedIds: [],
  bonusReasons: [],
  skipReason: null,
});
// 一个同步事务决定移动、吃子、奖励、胜利与轮转。旧动作明确拒绝。
export function dispatch(state, action) {
  const reject = (reason) => ({ ok: false, state, reason });
  if (
    action.matchId !== state.matchId ||
    action.expectedRevision !== state.revision ||
    action.actor !== state.currentPlayer
  )
    return reject("动作已过期或不是当前玩家");
  if (state.phase === "finished") return reject("对局已经结束");
  if (
    !["ROLL", "MOVE"].includes(action.type) ||
    (action.type === "ROLL"
      ? state.phase !== "awaitRoll"
      : state.phase !== "awaitMove")
  )
    return reject("当前阶段不能执行此动作");
  const move =
    action.type === "MOVE"
      ? legalMoves(state).find((m) => m.pieceId === action.pieceId)
      : null;
  if (action.type === "MOVE" && !move) return reject("棋子不能这样移动");
  const next = structuredClone(state);
  next.revision++;
  if (action.type === "ROLL") {
    // 掷骰只消耗独立RNG一次（含拒绝采样）；真实第三个6也保留在摘要。
    const draw = bounded(next.rng, 6);
    next.rng = draw.rng;
    next.dice = draw.value + 1;
    next.stats.rollCount++;
    next.sixStreak = next.dice === 6 ? next.sixStreak + 1 : 0;
    next.phase = "awaitMove";
    next.lastEvent = event("ROLL", action.actor, next.dice);
    if (next.sixStreak === 3 || !legalMoves(next).length) {
      next.lastEvent.skipReason = next.sixStreak === 3 ? "tripleSix" : "noMove";
      next.phase = "awaitRoll";
      next.dice = null;
      nextPlayer(next);
    }
  } else {
    const p = next.pieces.find((p) => p.id === move.pieceId);
    p.progress = move.to;
    // 只结算最终普通格：敌叠子全部回营，同色和安全格共存不受影响。
    for (const id of move.capturedIds)
      next.pieces.find((p) => p.id === id).progress = -1;
    next.stats.moveCount++;
    next.stats.captureCount += move.capturedIds.length;
    next.lastEvent = {
      ...event("MOVE", action.actor, next.dice),
      pieceId: p.id,
      from: move.from,
      to: move.to,
      capturedIds: move.capturedIds,
    };
    // 胜利优先于所有加掷；多个奖励原因仅决定一次留席，不累计队列。
    const win = homeCount(next, p.owner) >= targetCount(next);
    const reasons = bonusReasons(
      next.dice === 6,
      move.capturedIds.length > 0,
      move.to === 56,
      win,
    );
    next.lastEvent.bonusReasons = reasons;
    next.dice = null;
    if (win) {
      next.phase = "finished";
      next.winner = p.owner;
      next.sixStreak = 0;
    } else {
      next.phase = "awaitRoll";
      if (reasons.length) next.stats.bonusCount++;
      else nextPlayer(next);
    }
  }
  return { ok: true, state: next, reason: null };
}
export function makeAction(state, type, pieceId) {
  return {
    type,
    pieceId,
    matchId: state.matchId,
    expectedRevision: state.revision,
    actor: state.currentPlayer,
  };
}
