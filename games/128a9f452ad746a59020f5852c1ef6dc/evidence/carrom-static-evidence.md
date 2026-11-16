# E-01：只读源码证据索引

以下A/B路径均相对ref/，正文使用read_reference阅读。偏移与长度为字符，不是行号。摘录仅保存已读关键表达式；省略混淆键的展开，不声称完成字符串表解码或全文差分。

- A：mcp-inputs/mac-codex/4d4eab92df392599c54730b6e087a0949d4875f602c010358e18095007e2275d/Carrom_retry_4d4eab92.js
- B：mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js

## 检测与调用

A已读搜索区域包括169500起及其后连续分页，205000/7000覆盖BR尾部、helper与物理更新；B174000/5000、179000/24000与203000/8000覆盖搜索和helper。A其他搜索分页见会话记录；不把分页阅读当成全文词法检索。

helper签名：`_0x3ea989(_0x3e50b6, _0x192a9b, _0x372c57, _0x501ec4)`。

已读原表达式：
```
let _0x9e3c7c = { x: _0x3e50b6["x"], y: _0x3e50b6["y"] },
  _0x5b4ed9 = []
    [_0x5ef868(0x1c0)](_0x3e4566)
    ["concat"](_0x2a9c75, _0x3231b3);
```
循环使用`Math[_0x5ef868(0x1f8)](_0x501ec4 / _0x192a9b)`；先沿方向增加一步，再调用`_0x247dad(_0x9e3c7c, _0x5b4ed9, _0x192a9b * 0.9)`。后者逐枚比较`_0x2bd695(point,piece) < radius`。没有目标或移动子身份参数。

四函数：TL `_0x52106f`、TR `_0x25af2a`、BL `_0x521eef`、BR `_0x30849b`。每个已见四处调用：普通段、striker直击、striker反弹第一段、反弹第二段。

## fixture

A455500/4500：普通子共用构造器`_0x54e9a5`。
```
_0x19677d = 0x10
box2d["Circle"](_0x19677d / _0x541423, box2d[...](0x0, 0x0))
```
同段普通子`bullet: !![]`、`angularDamping: 0.2`、`linearDamping: 1.8`；body的objectType为`"puck"`。

A462000/1000与463000/6000：striker构造器`_0x13fb80`。
```
const _0x1c6272 = 0x22 * 0.8
shape = box2d[...]( (_0x1c6272 * 0.8) / _0x541423, ... )
```
body为dynamic，初始fixture为sensor；射击方法先`this["fixture"][...](false)`，唤醒body后施加冲量。get/set world位置使用`_0x541423`，update中位置乘`0x64`。因此圆半径分别为16px和21.76px，不以视觉sprite大小推断半径。

B451000/22000的已读内容覆盖相应构造器，未见上述几何半径差异。完整依赖版本和引擎实际slop未验证。

## 首选与重试

B156000/5000：四袋搜索在三种目标分支均传`!![]`启用普通出袋段检测；候选过滤使用`_0x133600 + 0x10`；首选力度：
```
(_0x321dde / 0x64) * 0x3c * 0.2 * 1.1 * 1.25
```
无候选成功fallback力度`0x64`。A同段已读表达式相同。

A169500/8000、B172000/2500：
```
// A
if (_carromRetryShot) _0xd6b627(_carromRetryShot, 100);
// B
if (_carromRetryShot) _0xd6b627(_carromRetryShot, _0x3e3780);
```
两者`++_carromAiRetryCount <= 2 ? _0x3d12d7() : null`；起点占用参数都是`_0x133600 + 0x10`。

A169500/8000、B174000/5000：open-baseline与fallback。fallback返回`{pos, dir}`，没有dist/hDot，也未调用路径检测。open-baseline将普通子在baseline上投影为区间，排序合并后找gap并重新调用占用检测；遇非finite坐标返回null。

## 袋口、边界、步长

袋口常量表达式已读并保存在会话记录第2181–2197行：x以320、630、26、30计算，y以500、636、26、30、124计算。得到TL(61,362)、TR(579,362)、BL(61,886)、BR(579,886)。

A61000/7000：四条static Edge位于table矩形内缩26px，除以100传入物理世界；真实table纹理宽高未取得。

A205000/7000及后续已读更新区：中心到袋口距离`<=0x14`判入袋；检测在world.step之前。已读step为`world.step(1/60,10,10)`。主ticker通过accumulator逐tick执行，实际慢帧表现未运行验证。

## 证据边界

未取得两份参考完整文件SHA256、全文调用词法检索或完整diff。目录路径中的哈希字符串不是本次计算的文件哈希。初次辅助脚本尝试读取工作区ref副本得到ENOENT；最终脚本已取消该读取，只以平台read_reference作为参考正文来源。不得将合成断言视为执行原游戏。
