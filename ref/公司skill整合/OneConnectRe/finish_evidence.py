from pathlib import Path
p=Path('开发说明.md');s=p.read_text(encoding='utf8').replace('固定棋盘多关测试结果见 `progress-board.txt`','固定棋盘多关测试结果见 `progress-board-final.txt`').replace('`progress-board.txt` 记录第 2 关','`progress-board-final.txt` 记录第 2 关');p.write_text(s,encoding='utf8')
