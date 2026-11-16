import { cellId } from './rules.js';
export const colors = ['blue', 'red', 'green', 'yellow'];
export const labels = ['蓝', '红', '绿', '黄'];
export const paints = ['#3275fa', '#dd253a', '#0cc737', '#ffc000'];
export const board = { x: 12, y: 126, width: 336, height: 335.4266211604096 };
export const nativeScale = 336 / 586;
export const cellSize = 336 / 15;
// 实际原版营地圆孔，不由理想网格的半格中心生成。
export const holes = [
  [
    [78.9, 431],
    [157, 430],
    [78.8, 508],
    [156.9, 508.1],
  ],
  [
    [78.9, 78],
    [156.6, 77.9],
    [78.8, 155],
    [156.9, 155.2],
  ],
  [
    [429.8, 77.6],
    [507.8, 77.6],
    [430, 153.6],
    [508, 153.5],
  ],
  [
    [429.9, 431],
    [507.9, 430.1],
    [429.9, 508.1],
    [508, 507.9],
  ],
];
export function nativePoint(u, v) {
  return { x: board.x + u * nativeScale, y: board.y + v * nativeScale };
}
export function gridPoint(row, col) {
  return nativePoint(((col + 0.5) * 586) / 15, ((row + 0.5) * 585) / 15);
}
export function geometry(manifest) {
  const grid = manifest.board.prototype_grid;
  const coordinates = [...grid.public_path, ...grid.private_paths.flat()];
  return {
    coordinates,
    point(piece, progress = piece.progress) {
      if (progress < 0)
        return nativePoint(...holes[piece.owner][Number(piece.id.split(':')[1]) - 1]);
      const [row, col] = coordinates[cellId(piece.owner, progress)];
      return gridPoint(row, col);
    },
  };
}
export const seats = [
  { x: 71, y: 502, diceX: 128 },
  { x: 71, y: 80, diceX: 128 },
  { x: 289, y: 80, diceX: 232 },
  { x: 289, y: 502, diceX: 232 },
];
export function movementPath(piece, from, to, geo) {
  const progress =
    from < 0 ? [-1, 0] : Array.from({ length: to - from + 1 }, (_, i) => from + i);
  return progress.map((p) => ({ ...geo.point(piece, p), progress: p }));
}
