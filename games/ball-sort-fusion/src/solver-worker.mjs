import { solve } from './rules.mjs';
// 求解在工作线程中执行，避免较难局面阻塞手势与动画。
self.onmessage = ({ data }) => self.postMessage({ id: data.id, ...solve(data.board, data.capacity, 350000) });
