"""Offline Onet analysis; bounded searches return unknown on exhaustion."""
from collections import Counter, deque

def _validate(board):
    if not isinstance(board, (list, tuple)) or not board or not isinstance(board[0], (list, tuple)) or not board[0]:
        raise ValueError('board must contain nonempty rows')
    cols = len(board[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != cols for row in board):
        raise ValueError('board must be rectangular')
    if any(type(v) is not int or v < 0 for row in board for v in row):
        raise ValueError('cells must be nonnegative integers')
    return len(board), cols

def can_connect(board, start, end):
    rows, cols = _validate(board)
    try:
        sr, sc = start
        er, ec = end
    except (TypeError, ValueError):
        raise ValueError('coordinates must be pairs') from None
    if any(type(v) is not int for v in (sr, sc, er, ec)):
        raise ValueError('coordinates must be integers')
    if not (0 <= sr < rows and 0 <= sc < cols and 0 <= er < rows and 0 <= ec < cols):
        return False
    if (sr, sc) == (er, ec) or not board[sr][sc] or board[sr][sc] != board[er][ec]:
        return False
    queue, seen = deque([(sr, sc, -1, 0)]), set()
    while queue:
        row, col, previous, turns = queue.popleft()
        for direction, (dr, dc) in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1))):
            nr, nc = row + dr, col + dc
            count = turns + int(previous != -1 and previous != direction)
            if count > 2 or not (-1 <= nr <= rows and -1 <= nc <= cols):
                continue
            if (nr, nc) == (er, ec):
                return True
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc]:
                continue
            key = (nr, nc, direction, count)
            if key not in seen:
                seen.add(key)
                queue.append(key)
    return False

def apply_fall(board, positions, direction):
    """Apply one C2 fall pass for each eliminated tile's column."""
    rows, cols = _validate(board)
    if direction not in (-1, 1):
        raise ValueError('fall direction must be -1 or 1')
    result = [list(row) for row in board]
    for row, col in positions:
        if not (0 <= row < rows and 0 <= col < cols):
            raise ValueError('position outside board')
        sequence = range(rows - 1, 0, -1) if direction == 1 else range(rows - 1)
        for target in sequence:
            source = target - direction
            if result[target][col] == 0 and result[source][col] != 0:
                result[target][col], result[source][col] = result[source][col], 0
    return result


def apply_move(board, positions, direction):
    """Apply one C2 move pass for each eliminated tile's row."""
    rows, cols = _validate(board)
    if direction not in (-1, 1):
        raise ValueError('move direction must be -1 or 1')
    result = [list(row) for row in board]
    for row, col in positions:
        if not (0 <= row < rows and 0 <= col < cols):
            raise ValueError('position outside board')
        sequence = range(cols - 1, 0, -1) if direction == 1 else range(cols - 1)
        for target in sequence:
            source = target - direction
            if result[row][target] == 0 and result[row][source] != 0:
                result[row][target], result[row][source] = result[row][source], 0
    return result


def apply_global_gravity(board, direction, bounds):
    """Compact the configured screen-space bounds using the runtime's 90° mapping."""
    rows, cols = _validate(board)
    if direction not in ('up', 'down', 'left', 'right'):
        raise ValueError('invalid global gravity direction')
    keys = {'top', 'left', 'rows', 'cols'}
    if (not isinstance(bounds, dict) or set(bounds) != keys or
        any(type(bounds[k]) is not int for k in keys) or
        bounds['top'] < 0 or bounds['left'] < 0 or bounds['rows'] < 1 or bounds['cols'] < 1 or
        bounds['top'] + bounds['rows'] > cols or bounds['left'] + bounds['cols'] > rows):
        raise ValueError('invalid gravity bounds')
    top, left, height, width = (bounds[k] for k in ('top', 'left', 'rows', 'cols'))
    if any(board[y][x] and not (left <= y < left + width and top <= cols - 1 - x < top + height)
           for y in range(rows) for x in range(cols)):
        raise ValueError('board exceeds gravity bounds')
    grid = [[board[left + c][cols - 1 - (top + r)] for c in range(width)] for r in range(height)]
    if direction in ('up', 'down'):
        for c in range(width):
            values = [grid[r][c] for r in range(height) if grid[r][c]]
            packed = ([0] * (height - len(values)) + values if direction == 'down'
                      else values + [0] * (height - len(values)))
            for r in range(height):
                grid[r][c] = packed[r]
    else:
        for r in range(height):
            values = [v for v in grid[r] if v]
            grid[r] = ([0] * (width - len(values)) + values if direction == 'right'
                       else values + [0] * (width - len(values)))
    result = [list(row) for row in board]
    for r in range(height):
        for c in range(width):
            result[left + c][cols - 1 - (top + r)] = grid[r][c]
    return result


def find_solution(board, max_nodes=10000, mode='static', gravity_bounds=None):
    rows, cols = _validate(board)
    if type(max_nodes) is not int or max_nodes < 0:
        raise ValueError('max_nodes must be a nonnegative integer')
    if mode not in ('static', 'fall_down', 'fall_up', 'move_right', 'move_left', 'gravity_down', 'gravity_up', 'gravity_left', 'gravity_right'):
        raise ValueError('unsupported board mode')
    if mode.startswith('gravity_'):
        apply_global_gravity(board, mode[8:], gravity_bounds)
    cells = tuple(v for row in board for v in row)
    if any(n % 2 for v, n in Counter(cells).items() if v):
        return {'status': 'unsolvable', 'moves': [], 'nodes': 0}
    nodes, dead = 0, set()
    def search(state):
        nonlocal nodes
        if not any(state):
            return []
        if state in dead:
            return None
        if nodes >= max_nodes:
            raise TimeoutError
        nodes += 1
        grid = [state[i * cols:(i + 1) * cols] for i in range(rows)]
        groups = {}
        for i, value in enumerate(state):
            if value:
                groups.setdefault(value, []).append(i)
        for indexes in groups.values():
            for offset, first in enumerate(indexes):
                for second in indexes[offset + 1:]:
                    a, b = divmod(first, cols), divmod(second, cols)
                    if can_connect(grid, a, b):
                        updated = list(state)
                        updated[first] = updated[second] = 0
                        if mode != 'static':
                            remaining_board = [updated[i * cols:(i + 1) * cols] for i in range(rows)]
                            if mode.startswith('gravity_'):
                                remaining_board = apply_global_gravity(remaining_board, mode[8:], gravity_bounds)
                            elif mode.startswith('fall_'):
                                remaining_board = apply_fall(remaining_board, (a, b), 1 if mode == 'fall_down' else -1)
                            else:
                                remaining_board = apply_move(remaining_board, (a, b), 1 if mode == 'move_right' else -1)
                            updated = [v for row in remaining_board for v in row]
                        rest = search(tuple(updated))
                        if rest is not None:
                            return [(a, b)] + rest
        dead.add(state)
        return None
    try:
        moves = search(cells)
    except TimeoutError:
        return {'status': 'unknown', 'moves': [], 'nodes': nodes}
    return {'status': 'solved' if moves is not None else 'unsolvable', 'moves': moves or [], 'nodes': nodes}

if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Analyze configured fixed boards without changing the game.')
    parser.add_argument('config', type=Path)
    parser.add_argument('--max-nodes', type=int, default=10000)
    parser.add_argument('--summary', action='store_true', help='omit individual moves')
    parser.add_argument('--fail-on', default='', help='comma-separated result statuses that should produce exit code 1')
    parser.add_argument('--mode', choices=('static', 'fall_down', 'fall_up', 'move_right', 'move_left', 'gravity_down', 'gravity_up', 'gravity_left', 'gravity_right', 'original'), default='static', help='board movement assumption; static is not valid for all game levels')
    args = parser.parse_args()
    fail_on = {value.strip() for value in args.fail_on.split(',') if value.strip()}
    allowed = {'solved', 'unsolvable', 'unknown', 'not_configured', 'invalid'}
    if fail_on - allowed:
        parser.error('unknown --fail-on status: ' + ', '.join(sorted(fail_on - allowed)))
    data = json.loads(args.config.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or not isinstance(data.get('levels'), list):
        parser.error('configuration must contain a levels list')
    results = []
    for entry in data['levels']:
        if not isinstance(entry, dict):
            parser.error('each level must be an object')
        if 'board' not in entry:
            results.append({'level': entry.get('level'), 'status': 'not_configured'})
            continue
        mode = args.mode
        if mode == 'original':
            level = entry.get('level')
            if type(level) is not int or level < 1:
                results.append({'level': level, 'status': 'invalid', 'error': 'positive level number required'})
                continue
            mode = entry.get('movement') or {1: 'static', 2: 'fall_down', 3: 'fall_up', 4: 'move_right', 0: 'move_left'}[level % 5]
        try:
            result = find_solution(entry['board'], args.max_nodes, mode, entry.get('gravity'))
        except ValueError as exc:
            results.append({'level': entry.get('level'), 'status': 'invalid', 'error': str(exc)})
        else:
            if args.summary:
                result = {**result, 'move_count': len(result['moves'])}
                del result['moves']
            results.append({'level': entry.get('level'), 'mode': mode, **result})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(result['status'] in fail_on for result in results):
        raise SystemExit(1)
