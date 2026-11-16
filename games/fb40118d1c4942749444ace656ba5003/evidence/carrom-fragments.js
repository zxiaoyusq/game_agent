// 从已实际读取的参考源码逐行摘录；仅供隔离诊断，不作为游戏产出。
// _0x4b3cc6：会话证据 L5222–5249；参考源码重建行号 L4345–4372。
function _0x4b3cc6(_0x412177, _0x3e3780, _0x323212) {
  var _carromBotShotTurn = _carromTurnId;
  if (!_0x3fddb3 || _carromAiShotTurn === _carromTurnId) return;
  if (!_0x412177 || !_0x412177.pos || !Number.isFinite(_0x412177.pos.x) || !Number.isFinite(_0x412177.pos.y) || !Number.isFinite(_0x412177.dir) || !Number.isFinite(_0x3e3780) || !Number.isFinite(_0x323212)) {
    if (_0x209883 === false) { _carromAiShotTurn = _carromTurnId; _0x24bb4a(); if (((_0x5d148e === 1 && _0x4268e2) || (_0x5d148e === 2 && _carromFreestyleQueenState.phase === "pending"))) { _carromAiShotTurn = _carromTurnId; _0x5ebd99 = false; _0xbdafb3(_carromTurnId); } else _0x5e7a5f(); }
    return;
  }
  if ((_0x412177._carromBoardSnapshot && _carromAiBoardChanged(_0x412177._carromBoardSnapshot)) || _0x412177.pos.x < _0x55e1a0 || _0x412177.pos.x > _0x187453 || _0x412177.pos.y !== _0x429ae3 || _0x23a7dc(_0x412177.pos, _0x133600 + 0x10)) {
    if (_carromAiRetryTurn !== _carromTurnId) { _carromAiRetryTurn = _carromTurnId; _carromAiRetryCount = 0; }
    var _carromRetryShot = ++_carromAiRetryCount <= 2 ? _0x3d12d7() : null;
    if (_carromRetryShot) _0xd6b627(_carromRetryShot, _0x3e3780);
    else { _0x24bb4a(); if (((_0x5d148e === 1 && _0x4268e2) || (_0x5d148e === 2 && _carromFreestyleQueenState.phase === "pending"))) { _carromAiShotTurn = _carromTurnId; _0x5ebd99 = false; _0xbdafb3(_carromTurnId); } else _0x5e7a5f(); }
    return;
  }
  _carromAiShotTurn = _carromTurnId;
  var _0x2643c5 = _0x157421;
  ((_0xc5bee4[_0x2643c5(0x197)] = ![]),
    (_0x27e1b4[_0x2643c5(0x294)] = _0x412177[_0x2643c5(0x4cf)]["x"]),
    (_0x27e1b4[_0x2643c5(0x1dd)] = _0x412177[_0x2643c5(0x4cf)]["y"]),
    _0x27e1b4[_0x2643c5(0x1cd)](
      _0x3e3780,
      Math["PI"] - _0x412177["dir"] + _0x323212,
    ),
    _0x24bb4a(),
    _0x338c29(function () {
      _0xbdafb3(_carromBotShotTurn);
    }, 0x8fc));
}
// _carromAiBoardChanged：会话证据 L5103–5123；重建 L4227–4247。
function _carromAiBoardChanged(snapshot) {
  if (!snapshot) return true;
  var savedByDisc = new Map();
  for (var i = 0; i < snapshot.length; i++) {
    var saved = snapshot[i];
    if (!saved || !saved.disc || savedByDisc.has(saved.disc)) return true;
    savedByDisc.set(saved.disc, saved);
  }
  var groups = [_0x3e4566, _0x2a9c75, _0x3231b3], count = 0;
  for (var groupIndex = 0; groupIndex < groups.length; groupIndex++) {
    for (var j = 0; j < groups[groupIndex].length; j++) {
      var disc = groups[groupIndex][j], entry = savedByDisc.get(disc);
      if (!disc || !entry || entry.group !== groupIndex || !Number.isFinite(disc.x) || !Number.isFinite(disc.y) ||
          !Number.isFinite(entry.x) || !Number.isFinite(entry.y) ||
          Math.abs(disc.x - entry.x) > 1 || Math.abs(disc.y - entry.y) > 1) return true;
      savedByDisc.delete(disc);
      count++;
    }
  }
  return count !== snapshot.length;
}
// _0x3ea989 与 _0x247dad：会话 L6152–6178；重建 L5274–5300。
function _0x3ea989(_0x3e50b6, _0x192a9b, _0x372c57, _0x501ec4) {
  var _0x5ef868 = _0x157421;
  let _0x9e3c7c = { x: _0x3e50b6["x"], y: _0x3e50b6["y"] },
    _0x5b4ed9 = []
      [_0x5ef868(0x1c0)](_0x3e4566)
      ["concat"](_0x2a9c75, _0x3231b3);
  for (
    let _0x290de6 = 0x0;
    _0x290de6 < Math[_0x5ef868(0x1f8)](_0x501ec4 / _0x192a9b);
    _0x290de6++
  ) {
    ((_0x9e3c7c["x"] += Math[_0x5ef868(0x430)](_0x372c57) * _0x192a9b),
      (_0x9e3c7c["y"] += Math[_0x5ef868(0x1c8)](_0x372c57) * _0x192a9b));
    if (_0x247dad(_0x9e3c7c, _0x5b4ed9, _0x192a9b * 0.9)) return !![];
  }
  return ![];
}
function _0x247dad(_0x250221, _0x1a62e0, _0x1f1c9e) {
  var _0x2ddb9c = _0x157421;
  for (
    let _0x567082 = 0x0;
    _0x567082 < _0x1a62e0[_0x2ddb9c(0x182)];
    _0x567082++
  ) {
    if (_0x2bd695(_0x250221, _0x1a62e0[_0x567082]) < _0x1f1c9e) return !![];
  }
  return ![];
}
