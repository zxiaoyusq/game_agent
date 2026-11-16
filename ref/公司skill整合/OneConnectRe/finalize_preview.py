from pathlib import Path
p=Path('build_preview.py');s=p.read_text(encoding='utf-8')
s=s.replace("('resumed.png','恢复对局','暂停界面点击三角播放按钮。')", "('resumed.png','恢复对局','暂停界面点击三角播放按钮。'),('failure.png','原版超时结算','完成一次配对后等待原版 5 分钟倒计时归零；缺少宿主 showAd 报错，此画面未出现主页按钮。')")
s=s.replace('目前未验证自然过关、后续关卡、结算和重开；','目前未验证自然过关及后续关卡；原版超时结算可见，但缺少宿主接口时未出现主页按钮，原版完整重开未通过；')
p.write_text(s,encoding='utf-8')
q=Path('阶段说明.md');t=q.read_text(encoding='utf-8-sig');t=t.replace('暂停、继续。暂停页', '暂停、继续；原版自然倒计时结束后进入结算，`showAd` 缺失报错，页面未显示主页按钮，无法认定重开通过。暂停页');t=t.replace('基线失败/重开及全流程回归','基线失败后的重开及全流程回归');t=t.replace('实验版以正常倒计时进入结算；','实验版以正常倒计时进入结算；10 秒实验版结算后返回菜单并重新开局；');q.write_text(t,encoding='utf-8')
