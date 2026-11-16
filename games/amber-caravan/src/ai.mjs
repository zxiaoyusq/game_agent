/** 商队 AI 只选择合法走法，不读取未来骰子，也不修改局面。 */
import { FINISH, getTokenCell, isSafeCell, legalMoves, moveToken } from './rules.mjs';

/** 估计对手下一骰能否截获目标；安全站和己方叠棋不受威胁。 */
function threatened(state, player, tokenIndex) {
  const cell = getTokenCell(player.id, player.tokens[tokenIndex], player.outerLast[tokenIndex]);
  if (cell === null || isSafeCell(cell)) return false;
  const allies = player.tokens.filter((progress, index) => getTokenCell(player.id, progress, player.outerLast[index]) === cell).length;
  if (allies >= 2) return false;
  return state.players.some((opponent) => opponent.id !== player.id && opponent.tokens.some((progress, index) => {
    const enemyCell = getTokenCell(opponent.id, progress, opponent.outerLast[index]);
    if (enemyCell === null) return false;
    const distance = (cell - enemyCell + 52) % 52;
    // 已开门的商队会进入自己的归航道，不再继续绕到门后的敌棋。
    const crossesHome = opponent.homeUnlocked && !opponent.outerLast[index] && progress + distance >= 51;
    return distance >= 1 && distance <= 6 && !crossesHome;
  }));
}

export function chooseMove(state) {
  const choices = legalMoves(state);
  if (choices.length === 0) return null;
  const player = state.players[state.turn];
  let best = choices[0];
  let bestScore = -Infinity;
  for (const tokenIndex of choices) {
    const result = moveToken(state, tokenIndex);
    const moved = result.players[state.turn];
    const action = result.lastAction;
    const cell = getTokenCell(player.id, moved.tokens[tokenIndex], moved.outerLast[tokenIndex]);
    let score = moved.tokens[tokenIndex] * 0.3;
    // 先结算，再截获解锁，随后在保护、出营与推进之间权衡。
    if (result.phase === 'won') score += 10000;
    if (action.to === FINISH) score += 1000;
    if (action.captured.length > 0) score += player.homeUnlocked ? 220 : 700;
    if (isSafeCell(cell)) score += 35;
    if (threatened(state, player, tokenIndex)) score += 30;
    if (threatened(result, moved, tokenIndex)) score -= 65;
    if (action.from === -1) score += 42;
    if (score > bestScore) {
      best = tokenIndex;
      bestScore = score;
    }
  }
  return best;
}
