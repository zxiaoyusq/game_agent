from pathlib import Path
p=Path('build_preview.py');s=p.read_text(encoding='utf8').replace('打开奖励箱后自然进入；本截图包含计时实验配置。','打开奖励箱后自然进入开发副本的第 2 关。');p.write_text(s,encoding='utf8')
p=Path('开发说明.md');s=p.read_text(encoding='utf-8-sig');s += '\n\n## 当前验证状态补充\n\n固定棋盘：`progress-board.txt` 记录第 2 关配置棋盘的逐对消除及第 3 关新配置棋盘加载，浏览器错误列表为空；`screenshots/board_level3.png` 为该测试画面。测试后已运行默认构建，当前 `game/data.js` 与基线 JSON 语义完全一致，`game/level-config.js` 没有默认覆盖。基线 84 个文件再次与原解包哈希核对，差异 0。\n\n真机视觉验收：BLOCKED。已发现并授权连接 Infinix X688B（Android 11，720×1640），但没有找到验收流程要求的 `vision-device-pipeline` 及其三个执行脚本。尚未执行真机游戏流程，不将浏览器证据当作真机验收。\n'
p.write_text(s,encoding='utf8')
