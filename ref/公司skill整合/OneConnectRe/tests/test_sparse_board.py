import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('oc_compile',ROOT/'tools/compile_levels.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=json.loads((ROOT/'baseline/data.js').read_text(encoding='utf8'))
class SparseBoards(unittest.TestCase):
 def test_sparse_even_board_is_accepted(self):
  board=[[0]*12 for _ in range(6)];board[2][4]=board[2][5]=1
  m.compile_data(source,{'levels':[{'level':1,'seconds':180,'board':board}]})
 def test_empty_and_unpaired_are_rejected(self):
  for board in ([[0]*12 for _ in range(6)], [[1]+[0]*11]+[[0]*12 for _ in range(5)]):
   with self.subTest(board=board),self.assertRaises(ValueError):m.compile_data(source,{'levels':[{'level':1,'seconds':180,'board':board}]})
if __name__=='__main__':unittest.main()
