import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from board_solver import can_connect, find_solution

class BoardSolverTests(unittest.TestCase):
    def test_direct_and_empty_cells(self):
        self.assertTrue(can_connect([[1, 0, 1]], (0, 0), (0, 2)))
        self.assertFalse(can_connect([[1, 0, 2]], (0, 0), (0, 2)))
        self.assertFalse(can_connect([[1]], (0, 0), (0, 0)))

    def test_outside_ring_and_blocked_routes(self):
        board = [[1, 2, 1], [2, 3, 3]]
        self.assertTrue(can_connect(board, (0, 0), (0, 2)))
        self.assertFalse(can_connect(board, (1, 0), (0, 1)))

    def test_solution_is_a_replayable_path(self):
        board = [[1, 2, 1], [2, 3, 3]]
        original = [row[:] for row in board]
        result = find_solution(board, max_nodes=10000)
        self.assertEqual(result['status'], 'solved')
        self.assertEqual(board, original)
        for a, b in result['moves']:
            self.assertTrue(can_connect(board, a, b))
            board[a[0]][a[1]] = board[b[0]][b[1]] = 0
        self.assertFalse(any(map(any, board)))

    def test_even_counts_can_still_be_unsolvable(self):
        self.assertEqual(find_solution([[1, 2], [2, 1]], max_nodes=100)['status'], 'unsolvable')

    def test_odd_counts_not_solvable(self):
        self.assertEqual(find_solution([[1, 2]], max_nodes=100)['status'], 'unsolvable')

    def test_exhausted_search_is_unknown(self):
        self.assertEqual(find_solution([[1, 1]], max_nodes=0)['status'], 'unknown')

    def test_rejects_malformed_boards(self):
        for bad in ([], [[1], [1, 1]], [[-1, -1]], [[True, True]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                find_solution(bad, max_nodes=100)


class GravityTests(unittest.TestCase):
    def test_global_gravity_uses_screen_coordinates_and_bounds(self):
        from board_solver import apply_global_gravity
        board = [[1, 0, 2], [0, 0, 0]]
        bounds = {'top': 0, 'left': 0, 'rows': 3, 'cols': 2}
        self.assertEqual(apply_global_gravity(board, 'down', bounds), [[1, 2, 0], [0, 0, 0]])
        self.assertEqual(apply_global_gravity(board, 'up', bounds), [[0, 1, 2], [0, 0, 0]])
        self.assertEqual(apply_global_gravity(board, 'left', bounds), board)
        self.assertEqual(apply_global_gravity(board, 'right', bounds), [[0, 0, 0], [1, 0, 2]])
        self.assertEqual(board, [[1, 0, 2], [0, 0, 0]])
        with self.assertRaises(ValueError):
            apply_global_gravity(board, 'down', {'top': 1, 'left': 0, 'rows': 2, 'cols': 2})

    def test_global_gravity_solution_replays(self):
        from board_solver import apply_global_gravity
        bounds = {'top': 0, 'left': 0, 'rows': 2, 'cols': 2}
        for direction in ('down', 'up', 'left', 'right'):
            board = [[1, 2], [1, 2]]
            result = find_solution(board, mode='gravity_' + direction, gravity_bounds=bounds)
            self.assertEqual(result['status'], 'solved')
            for a, b in result['moves']:
                self.assertTrue(can_connect(board, a, b))
                board[a[0]][a[1]] = board[b[0]][b[1]] = 0
                board = apply_global_gravity(board, direction, bounds)
            self.assertFalse(any(map(any, board)))

    def test_fall_only_affected_columns(self):
        from board_solver import apply_fall
        board = [[1, 2, 3], [4, 5, 6], [0, 0, 0]]
        result = apply_fall(board, [(2, 0), (2, 2)], 1)
        self.assertEqual(result, [[0, 2, 0], [1, 5, 3], [4, 0, 6]])
        self.assertEqual(board, [[1, 2, 3], [4, 5, 6], [0, 0, 0]])

    def test_two_removed_tiles_in_same_column_cause_two_passes(self):
        from board_solver import apply_fall
        board = [[1], [2], [0], [0]]
        self.assertEqual(apply_fall(board, [(2, 0), (3, 0)], 1), [[0], [0], [1], [2]])

    def test_dynamic_solution_can_be_replayed_with_fall(self):
        from board_solver import apply_fall
        board = [[1, 2], [1, 2], [3, 3]]
        result = find_solution(board, max_nodes=1000, mode='fall_down')
        self.assertEqual(result['status'], 'solved')
        for a, b in result['moves']:
            self.assertTrue(can_connect(board, a, b))
            board[a[0]][a[1]] = board[b[0]][b[1]] = 0
            board = apply_fall(board, [a, b], 1)
        self.assertFalse(any(map(any, board)))

class HorizontalTests(unittest.TestCase):
    def test_only_selected_rows_shift_right(self):
        from board_solver import apply_move
        board = [[1, 2, 0], [3, 4, 5], [6, 7, 0]]
        result = apply_move(board, [(0, 2), (2, 2)], 1)
        self.assertEqual(result, [[0, 1, 2], [3, 4, 5], [0, 6, 7]])
        self.assertEqual(board, [[1, 2, 0], [3, 4, 5], [6, 7, 0]])

    def test_same_row_shifts_twice_to_left(self):
        from board_solver import apply_move
        self.assertEqual(apply_move([[0, 0, 1, 2]], [(0, 0), (0, 1)], -1), [[1, 2, 0, 0]])

    def test_dynamic_right_and_left_solutions_replay(self):
        from board_solver import apply_move
        for mode, direction in [('move_right', 1), ('move_left', -1)]:
            with self.subTest(mode=mode):
                board = [[1, 2], [1, 2], [3, 3]]
                result = find_solution(board, max_nodes=1000, mode=mode)
                self.assertEqual(result['status'], 'solved')
                for a, b in result['moves']:
                    self.assertTrue(can_connect(board, a, b))
                    board[a[0]][a[1]] = board[b[0]][b[1]] = 0
                    board = apply_move(board, [a, b], direction)
                self.assertFalse(any(map(any, board)))

if __name__ == '__main__':
    unittest.main()
