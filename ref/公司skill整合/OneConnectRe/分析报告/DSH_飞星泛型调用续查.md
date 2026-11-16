# 飞星调用和道具锁定续查

请继续仅离线、非多模态追查上一份 `飞星轨迹与道具界面_补充拆解.md` 的实现阻塞，勿操作模拟器或修改 One Connect：

1. 解析 genericMethodPointers / Il2CppGenericMethod 映射或直接检查 0x1C49C00、0x1C499F0、0x1C49110 的方法体，确定它们是否分别为 SetEase、SetDelay、OnComplete；修正 Ease 枚举常量表并直接核验 5 的含义。给出可复跑证据。
2. 逐函数追踪从 DrawLinkStar 到 CreateStar 与移动 tween，确认移动是否确有曲线路径或其他会改变星坐标的父节点/动画；若 DOLocalMove 只表示线性插值，不要称作曲线。明确多星生成间隔和触发顺序。
3. 追查 PropControl 初始化和按钮 Lock 的显隐、魔法棒解锁条件；报告无法证实的项。不要推断看广告/购买行为，且不实现内购。
4. 更新原报告和机器可读参数，逐项标出指令、资源、推断与未知；若无法解析解释具体阻碍，保留现有证据。
