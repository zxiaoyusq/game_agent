import json
import random
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from board_solver import find_solution

class SolverParity(unittest.TestCase):
    def test_python_and_js_agree_on_deterministic_small_boards(self):
        rng=random.Random(77413)
        samples=[]
        for level in range(1,6):
            for _ in range(5):
                tiles=[1,1,2,2,3,3,4,4];rng.shuffle(tiles)
                samples.append({'board':[tiles[:4],tiles[4:]],'level':level})
        js="const fs=require('fs'),vm=require('vm');let c={};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);let x=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(x.map(z=>c.solveBoard(z.board,z.level,500))))"
        result=subprocess.run(['node','-e',js,str(ROOT/'tools/board_solver.js')],input=json.dumps(samples),text=True,encoding='utf8',capture_output=True,check=True,cwd=ROOT.parent)
        actual=json.loads(result.stdout)
        modes=['static','fall_down','fall_up','move_right','move_left']
        for spec,got in zip(samples,actual):
            expected=find_solution(spec['board'],500,modes[spec['level']-1])
            self.assertEqual((got['status'],got['nodes']),(expected['status'],expected['nodes']))
            self.assertEqual(got['moves'],json.loads(json.dumps(expected['moves'])))

if __name__=='__main__': unittest.main()
