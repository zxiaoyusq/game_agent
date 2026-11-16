import { legalMoves } from "./rules.js";
// 词典序固定策略；只读合法动作，不窥视未来骰子。
export function chooseMove(state, moves = legalMoves(state)) {
  const score = (m) => [
    Number(m.to === 56),
    m.capturedIds.length,
    Number(m.from === -1),
    Number(m.safe),
    m.to,
    -Number(m.pieceId.split(":")[1]),
  ];
  return (
    moves.slice().sort((a, b) => {
      const x = score(a),
        y = score(b);
      for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return y[i] - x[i];
      return 0;
    })[0] ?? null
  );
}
