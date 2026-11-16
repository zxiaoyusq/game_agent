# Android WebView 预览验证

该目录包含仅供开发回归使用的临时 WebView 测试壳源码和本机签名的 `out/preview.apk`。它通过 `http://127.0.0.1:18749/game/game.html` 访问运行中的 PC 开发服务；不是游戏发布包、AHA 宿主或真实广告 SDK。

运行前，从工程根目录启动 `启动开发预览.cmd` 并确认服务使用 18749 端口；选择独立 Android 测试设备，确认不会占用其他任务。将下面的 `<serial>` 替换为 `adb devices -l` 返回的明确序列号：

```powershell
& 'C:\Program Files\ADB\adb.exe' -s '<serial>' reverse tcp:18749 tcp:18749
& 'C:\Program Files\ADB\adb.exe' -s '<serial>' install --no-incremental tests\android_preview\out\preview.apk
& 'C:\Program Files\ADB\adb.exe' -s '<serial>' shell am start -n local.oneconnect/.MainActivity
```

测试壳包含窗口标题栏，截图里的上方状态栏与标题栏不是游戏 UI。截图应注明设备、引擎、操作步骤和是否模拟触控。完成后可卸载这次安装的测试包，并移除本次 reverse；不要删除其他应用或切换其他任务的设备。

```powershell
& 'C:\Program Files\ADB\adb.exe' -s '<serial>' uninstall local.oneconnect
& 'C:\Program Files\ADB\adb.exe' -s '<serial>' reverse --remove tcp:18749
```

`natural_progress.cjs` 是一次动物主题自动操作证据：WebView 调试接口只读取棋盘和运行状态，选择可连牌后通过 ADB 坐标点击，未写入棋盘或强制胜利。脚本中的设备序列号、端口、屏幕偏移和尺寸是本次 MuMu 设备专用，重新使用必须先确认并调整；它不是通用真机验收脚本。调试开启仅用于本测试壳，不应直接用于发布应用。

AHA 宿主、真实手机、平台广告与所有页面仍需分别验证，不可用该预览壳替代。
