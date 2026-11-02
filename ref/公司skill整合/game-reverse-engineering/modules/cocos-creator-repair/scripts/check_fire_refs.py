#!/usr/bin/env python3
"""检查 Cocos .fire 场景文件的父子引用完整性。

用法: python check_fire_refs.py <scene.fire>
输出: 自引用 / 悬空 parent / parent-children 不一致 的节点清单。

栈溢出 (_initProperties) 的直接原因就是这些引用问题。
"""
import json
import sys


def main(path: str) -> int:
    try:
        data = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        print(f"文件不存在: {path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return 1

    issues = []
    nodes = {}

    for i, obj in enumerate(data):
        if not isinstance(obj, dict):
            continue
        if obj.get("__type__") == "cc.Node":
            nodes[i] = obj

    for i, node in nodes.items():
        name = node.get("_name", "?")
        children = [c.get("__id__") for c in node.get("_children", [])] if node.get("_children") else []
        parent = node.get("_parent")
        pid = parent.get("__id__") if isinstance(parent, dict) else None

        if i in children:
            issues.append(f"[{i}] '{name}' 自引用: children 包含自己")
        if pid is not None and pid != 1:  # 1 = Scene
            if pid not in nodes:
                issues.append(f"[{i}] '{name}' parent={pid} 悬空引用")
            else:
                pkids = [c.get("__id__") for c in nodes[pid].get("_children", [])] if nodes[pid].get("_children") else []
                if i not in pkids:
                    issues.append(f"[{i}] '{name}' parent={pid}('{nodes[pid].get('_name','?')}') 但 parent.children 缺失该节点")

    if issues:
        print(f"发现 {len(issues)} 个引用问题:")
        for x in issues:
            print(f"  !!! {x}")
        return 2
    else:
        print("OK: 父子引用一致")
        return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_fire_refs.py <scene.fire>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
