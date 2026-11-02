#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frida_capture_eval.py -- Frida 运行时代码捕获（eval / require / Function）

用途：往真机/模拟器的 JSB 进程注入 Frida 脚本，捕获运行时动态拼出的 JS 源码
      （eval、new Function、require 加载的模块内容、console 传入的长字符串），
      用于还原被加密/混淆/远程加载的玩法逻辑与 Trait 目录名，互补于
      extract_js_from_heap.py（堆静态切窗）。

用法：
  python frida_capture_eval.py --device <serial or "local"> --package <com.example.game> \\
      --out frida_capture/ --attach-delay 3
  python frida_capture_eval.py --package com.example.game --out out/ --spawn \\
      --hook-eval --hook-require --hook-function --min-len 80

依赖：pip install frida-tools；需要进程未 root 也可（spawn + gadget 除外），
      root 设备更稳定。默认 hook 规则与偏移值属于示例，请按目标项目调整。
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FRIDA_JS = r"""
'use strict';
var minLen = %(min_len)d;
var out = [];
function push(tag, s) {
  try { if (typeof s === 'string' && s.length >= minLen) {
    out.push({tag: tag, len: s.length, head: s.slice(0, 400)});
    if (out.length > 500) out.shift();
  } } catch (e) {}
}
%(hook_eval)s
%(hook_require)s
%(hook_function)s
setInterval(function () {
  send({type: 'flush', items: out});
  out = [];
}, 2000);
"""
# 示例 hook 片段：每个可开关；实际项目可替换为更精确的 JS 入口
EVAL_HOOK = """
if (typeof globalThis.eval === 'function') {
  var _eval = globalThis.eval;
  globalThis.eval = function (code) {
    push('eval', code);
    return _eval.apply(this, arguments);
  };
}
"""
REQUIRE_HOOK = """
try {
  var _req = globalThis.require || globalThis.__require;
  if (typeof _req === 'function') {
    var _orig = _req;
    globalThis.require = function (id) {
      try { push('require:' + id, _orig.call(this, id)); } catch (e) {}
      return _orig.apply(this, arguments);
    };
  }
} catch (e) {}
"""
FUNCTION_HOOK = """
if (typeof Function === 'function') {
  var _F = Function;
  globalThis.Function = function () {
    push('Function', String(arguments[arguments.length - 1]));
    return _F.apply(this, arguments);
  };
}
"""


def make_script(args):
    js = FRIDA_JS % {
        "min_len": args.min_len,
        "hook_eval": EVAL_HOOK if args.hook_eval else "",
        "hook_require": REQUIRE_HOOK if args.hook_require else "",
        "hook_function": FUNCTION_HOOK if args.hook_function else "",
    }
    return js


def main():
    ap = argparse.ArgumentParser(description="Frida 运行时捕获 JS")
    ap.add_argument("--device", default="", help="frida设备序列号（缺省本地USB）")
    ap.add_argument("--package", required=True, help="目标包名")
    ap.add_argument("--out", default="frida_capture/")
    ap.add_argument("--attach-delay", type=float, default=2.0)
    ap.add_argument("--spawn", action="store_true")
    ap.add_argument("--hook-eval", action="store_true", default=True)
    ap.add_argument("--hook-require", action="store_true", default=True)
    ap.add_argument("--hook-function", action="store_true")
    ap.add_argument("--min-len", type=int, default=80)
    ap.add_argument("--seconds", type=int, default=30)
    args = ap.parse_args()

    try:
        import frida
    except ImportError:
        print("[fatal] 需要 frida：pip install frida-tools", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True)
    script_js = make_script(args)
    try:
        device = frida.get_usb_device() if not args.device else frida.get_device(args.device)
        if args.spawn:
            pid = device.spawn([args.package])
            session = device.attach(pid)
            device.resume(pid)
        else:
            session = device.attach(args.package)
    except Exception as exc:
        print(f"[fatal] frida 连接/挂载失败：{exc}", file=sys.stderr)
        print("[提示] 确认设备在线（adb devices / frida-ps -U）、目标 App 已启动、包名与 --package 一致。", file=sys.stderr)
        sys.exit(2)

    collected = []
    def on_message(msg, data):
        if msg.get("type") == "send":
            payload = msg.get("payload", {})
            if isinstance(payload, dict) and payload.get("type") == "flush":
                collected.extend(payload.get("items", []))
        elif msg.get("type") == "error":
            print("[frida error]", msg.get("description"), file=sys.stderr)

    script = session.create_script(script_js)
    script.on("message", on_message)
    script.load()
    print("[*] attached; capturing %d s (Ctrl+C to stop earlier)" % args.seconds, file=sys.stderr)
    import time
    try:
        time.sleep(args.seconds)
    except KeyboardInterrupt:
        pass
    script.unload()
    with open(os.path.join(args.out, "frida_capture.json"), "w", encoding="utf-8") as fh:
        json.dump({"package": args.package, "items": collected}, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"items": len(collected), "out": os.path.join(args.out, "frida_capture.json")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
