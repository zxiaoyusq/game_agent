from pathlib import Path
p=Path('build_preview.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("('experiment_board.png','实验计时','选择动物主题后显示约 0:58，验证初始 60 秒生效。')", "('experiment_board.png','实验计时','选择动物主题后显示约 0:58，验证初始 60 秒生效。'),('experiment_timeout.png','实验版超时结算','将初始计时改为 60 秒，等待倒计时自然归零；本次以本地模拟宿主接口运行。'),('quick_home.png','实验版返回菜单','10 秒实验版计时结束后点击结算页的主页按钮。'),('quick_restart.png','实验版重新开始','返回菜单后重新点击开始并选择主题，进入新一局。')")
p.write_text(s,encoding='utf-8')
