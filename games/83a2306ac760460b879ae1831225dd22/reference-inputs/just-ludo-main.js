window.__require = (function e(t, n, o) {
  function a(r, s) {
    if (!n[r]) {
      if (!t[r]) {
        var c = r.split("/");
        if (((c = c[c.length - 1]), !t[c])) {
          var l = "function" == typeof __require && __require;
          if (!s && l) return l(c, !0);
          if (i) return i(c, !0);
          throw new Error("Cannot find module '" + r + "'");
        }
        r = c;
      }
      var u = (n[r] = { exports: {} });
      t[r][0].call(
        u.exports,
        function (e) {
          return a(t[r][1][e] || e);
        },
        u,
        u.exports,
        e,
        t,
        n,
        o
      );
    }
    return n[r].exports;
  }
  for (
    var i = "function" == typeof __require && __require, r = 0;
    r < o.length;
    r++
  )
    a(o[r]);
  return a;
})(
  {
    ADRewardView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "e4edfteNbFGX5fUuttbzkDh", "ADRewardView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Manager/UserInfoManager"),
          p = e("../Framework/Native/NativeBridge"),
          f = e("../Framework/Utils/Utils"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labCoinsLeftCount = null),
                (t.labDiamondsLeftCount = null),
                (t.labCoins = null),
                (t.labDiamonds = null),
                (t.btnCoins = null),
                (t.btnDiamonds = null),
                (t._leftCoins = 0),
                (t._leftDiamonds = 0),
                (t._coinsLeftCount = 5),
                (t._diamondsLeftCount = 5),
                (t._coinsADCountIdx = 0),
                (t._diamondsADCountIdx = 0),
                (t._getCoinsArray = [200, 300, 400, 500, 600]),
                (t._getDiamondsArray = [2, 3, 4, 5, 6]),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                f.default.localStr(this.node);
                for (var e = 0; e < this._getCoinsArray.length; e++)
                  this._leftCoins += this._getCoinsArray[e];
                for (e = 0; e < this._getDiamondsArray.length; e++)
                  this._leftDiamonds += this._getDiamondsArray[e];
                (this.labCoins.string =
                  this._getCoinsArray[this._coinsADCountIdx].toString()),
                  (this.labDiamonds.string =
                    this._getDiamondsArray[
                      this._diamondsADCountIdx
                    ].toString()),
                  (this.labCoinsLeftCount.string =
                    "x" + this._coinsLeftCount.toString()),
                  (this.labDiamondsLeftCount.string =
                    "x" + this._diamondsLeftCount.toString()),
                  p.default.preloadReward(s.ADType.ADRewardCoins);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.onClickCoins = function () {
                var e = this;
                if (
                  (c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                  u.default.getInstance().getTools().showNoNetWorkTip())
                ) {
                  var t = this._coinsADCountIdx + 1,
                    n = this._getCoinsArray[t - 1];
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedPointKey.ADReward,
                      rewardType: s.ADRewardType.Coins,
                      reward: n,
                    }),
                    p.default.watchVideo(function () {
                      e._coinsADCountIdx += 1;
                      var t = e._getCoinsArray[e._coinsADCountIdx - 1];
                      (e._leftCoins -= t),
                        e._coinsADCountIdx > 4 && (e._coinsADCountIdx = 4),
                        (e.labCoins.string =
                          e._getCoinsArray[e._coinsADCountIdx].toString()),
                        (e._coinsLeftCount -= 1),
                        (e.labCoinsLeftCount.string =
                          "x" + e._coinsLeftCount.toString()),
                        0 == e._coinsLeftCount &&
                          (e.btnCoins.interactable = !1);
                      var n = u.default.getInstance().getHallGoldPos(),
                        o = f.default.getWorldPosition(e.btnCoins.node);
                      u.default
                        .getInstance()
                        .getTools()
                        .playFlyEffect(
                          s.FlyEffectType.Coins,
                          n,
                          t,
                          function () {
                            var e = d.default.getInstance().getMyselfUserInfo();
                            e.setGoldNum(e.getGoldNum() + t);
                          },
                          o
                        );
                    }, s.ADType.ADRewardCoins);
                }
              }),
              (t.prototype.onClickDiamonds = function () {
                var e = this;
                if (
                  (c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                  u.default.getInstance().getTools().showNoNetWorkTip())
                ) {
                  var t = this._diamondsADCountIdx + 1,
                    n = this._getDiamondsArray[t - 1];
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedPointKey.ADReward,
                      rewardType: s.ADRewardType.Diamonds,
                      reward: n,
                    }),
                    p.default.watchVideo(function () {
                      e._diamondsADCountIdx += 1;
                      var t = e._getDiamondsArray[e._diamondsADCountIdx - 1];
                      (e._leftDiamonds -= t),
                        e._diamondsADCountIdx > 4 &&
                          (e._diamondsADCountIdx = 4),
                        (e.labDiamonds.string =
                          e._getDiamondsArray[
                            e._diamondsADCountIdx
                          ].toString()),
                        (e._diamondsLeftCount -= 1),
                        (e.labDiamondsLeftCount.string =
                          "x" + e._diamondsLeftCount.toString()),
                        0 == e._diamondsLeftCount &&
                          (e.btnDiamonds.interactable = !1);
                      var n = u.default.getInstance().getHallDiamondPos(),
                        o = f.default.getWorldPosition(e.btnDiamonds.node);
                      u.default
                        .getInstance()
                        .getTools()
                        .playFlyEffect(
                          s.FlyEffectType.Diamonds,
                          n,
                          t,
                          function () {
                            var e = d.default.getInstance().getMyselfUserInfo();
                            e.setDiamondNum(e.getDiamondNum() + t);
                          },
                          o
                        );
                    }, s.ADType.ADRewardDiamond);
                }
              }),
              (t.prototype.onClickClose = function () {
                this.onClose(), cc.director.emit(s.GameEvent.Show_Popular_View);
              }),
              i([m(cc.Label)], t.prototype, "labCoinsLeftCount", void 0),
              i([m(cc.Label)], t.prototype, "labDiamondsLeftCount", void 0),
              i([m(cc.Label)], t.prototype, "labCoins", void 0),
              i([m(cc.Label)], t.prototype, "labDiamonds", void 0),
              i([m(cc.Button)], t.prototype, "btnCoins", void 0),
              i([m(cc.Button)], t.prototype, "btnDiamonds", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    AdLoading: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "6af0d5MrGNPfoEPNckk/pFf", "AdLoading");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = cc._decorator,
          l = c.ccclass,
          u = c.property,
          d = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.loadingAnim = null),
                (t.labProgress = null),
                (t._finishCallback = null),
                (t._durationSecond = 6),
                (t._totoalProgress = 100),
                (t._curProgress = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  s.GameEvent.AD_Cache_Success,
                  this.onADCacheSuccess,
                  this
                ),
                  this.registerEvent(
                    s.GameEvent.AD_Cache_Fail,
                    this.onADCacheFail,
                    this
                  );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.startLoading = function (e) {
                this._finishCallback = e;
                var t = this._durationSecond / this._totoalProgress;
                this.schedule(this.loadingTimer, t),
                  (this.labProgress.string = "0"),
                  this.loadingAnim.play("adloading");
              }),
              (t.prototype.loadingTimer = function () {
                (this._curProgress += 1),
                  this._curProgress >= this._totoalProgress
                    ? ((this.labProgress.string = this._curProgress.toString()),
                      this.closeTimer(),
                      this._finishCallback && this._finishCallback(),
                      this.onClose(!1))
                    : (this.labProgress.string = this._curProgress.toString());
              }),
              (t.prototype.closeTimer = function () {
                this.unschedule(this.loadingTimer), (this._curProgress = 0);
              }),
              (t.prototype.onADCacheSuccess = function () {
                this.onClose();
              }),
              (t.prototype.onADCacheFail = function () {
                this.onClose();
              }),
              i([u(cc.Animation)], t.prototype, "loadingAnim", void 0),
              i([u(cc.Label)], t.prototype, "labProgress", void 0),
              i([l], t)
            );
          })(r.default);
        (n.default = d), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
      },
    ],
    Add_Player_Tips: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "30e729w5+RLuJUdD5KXdIww", "Add_Player_Tips");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Utils/Utils"),
          c = cc._decorator,
          l = c.ccclass,
          u = c.property,
          d = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.label_txt = null),
                (t._callback = null),
                (t._addBaseNode = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                s.default.localStr(this.node);
              }),
              (t.prototype.showView = function (e, t, n, o) {
                (this._callback = e), (this._addBaseNode = t);
                var a = s.default.replaceStr(
                  ["game_bule", "game_red", "game_green", "game_yellow"][o]
                );
                this.label_txt.string = n
                  ? s.default.replaceStr("game_add", a)
                  : s.default.replaceStr("game_remove", a);
              }),
              (t.prototype.onBtnOkClick = function () {
                this._callback && this._callback(),
                  (this._addBaseNode.active = !0),
                  this.onClose();
              }),
              (t.prototype.onBtnCloseClick = function () {
                (this._addBaseNode.active = !0), this.onClose();
              }),
              i([u(cc.Label)], t.prototype, "label_txt", void 0),
              i([l], t)
            );
          })(r.default);
        (n.default = d), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    Add_Player: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "dedfa95Q05CkaZc5SMtj+Jy", "Add_Player");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Utils/Utils"),
          p = e("./Add_Player_Tips"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.add_list = []),
                (t.del_list = []),
                (t.node_base = null),
                (t.add_base = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                d.default.localStr(this.node), this.updateView();
              }),
              (t.prototype.updateView = function () {
                for (
                  var e = u.default.getInstance().getLocalInfo(),
                    t = Object.keys(e).length,
                    n = 0;
                  n < 4;
                  n++
                )
                  e[n]
                    ? t > 2
                      ? ((this.add_list[n].active = !1),
                        (this.del_list[n].active = !0))
                      : ((this.add_list[n].active = !1),
                        (this.del_list[n].active = !1))
                    : ((this.add_list[n].active = !0),
                      (this.del_list[n].active = !1));
              }),
              (t.prototype.onBtnAddClick = function (e, t) {
                var n = this,
                  o = parseInt(t);
                this.loadRes(
                  s.GAME_PREFAB_PATH + "Add_Player_Tips",
                  cc.Prefab,
                  function (e) {
                    var t = cc.instantiate(e);
                    t.parent = n.node_base;
                    var a = t.getComponent(p.default);
                    (n.add_base.active = !1),
                      a.showView(
                        function () {
                          u.default.getInstance().setLocalInfo(o, !1, !1),
                            cc.director.emit(c.GameEvent.Add_Player, o),
                            l.default
                              .getInstance()
                              .sendBuriedPointInfo({
                                event: c.BuriedOneKey.localGameRoom,
                                actionName: c.BuriedTwoKey.addBtnClick,
                                playerIndex: o,
                              }),
                            n.updateView();
                        },
                        n.add_base,
                        !0,
                        o
                      );
                  }
                );
              }),
              (t.prototype.onBtnDelClick = function (e, t) {
                var n = this,
                  o = parseInt(t);
                this.loadRes(
                  s.GAME_PREFAB_PATH + "Add_Player_Tips",
                  cc.Prefab,
                  function (e) {
                    var t = cc.instantiate(e);
                    t.parent = n.node;
                    var a = t.getComponent(p.default);
                    (n.add_base.active = !1),
                      a.showView(
                        function () {
                          u.default.getInstance().deleLocalInfo(o),
                            cc.director.emit(c.GameEvent.Del_Player, o),
                            l.default
                              .getInstance()
                              .sendBuriedPointInfo({
                                event: c.BuriedOneKey.localGameRoom,
                                actionName: c.BuriedTwoKey.removeBtnClick,
                                playerIndex: o,
                              }),
                            n.updateView();
                        },
                        n.add_base,
                        !1,
                        o
                      );
                  }
                );
              }),
              i([g(cc.Node)], t.prototype, "add_list", void 0),
              i([g(cc.Node)], t.prototype, "del_list", void 0),
              i([g(cc.Node)], t.prototype, "node_base", void 0),
              i([g(cc.Node)], t.prototype, "add_base", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Utils/Utils": "Utils",
        "./Add_Player_Tips": "Add_Player_Tips",
      },
    ],
    AtlasResManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "ec7a8cwKvZIR4NToX0J84xR", "AtlasResManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameEnum"),
          a = (function () {
            function e() {
              (this._atlasResList = []),
                (this.isLoadHallPrefab = !1),
                (this.isLoadGamePrefan = !1);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.loadAtlasRes = function (e) {
                var t = this;
                cc.loader.loadResArray(
                  [
                    "Texture/atlas/Main_Cmn",
                    "Texture/atlas/original1",
                    "Texture/atlas/cupActivity",
                  ],
                  cc.SpriteAtlas,
                  function (n, o) {
                    if (o) {
                      for (var a = 0; a < o.length; a++)
                        t._atlasResList.push(o[a]);
                      e && e(o);
                    }
                  }
                );
              }),
              (e.prototype.getSpriteFrame = function (e) {
                for (var t = null, n = 0; n < this._atlasResList.length; n++)
                  if (this._atlasResList[n].getSpriteFrame(e)) {
                    t = this._atlasResList[n].getSpriteFrame(e);
                    break;
                  }
                return t;
              }),
              (e.prototype.loadRoomPrefab = function (e, t, n) {
                cc.loader.loadResArray(
                  [
                    "Prefab/Hall/prefab/computerPlayCountView",
                    "Prefab/Hall/prefab/computerRoomView",
                    "Prefab/Hall/prefab/RoomInfoView",
                    "Prefab/Hall/prefab/LocalRoomView",
                    "Prefab/Hall/prefab/WatchADOutView",
                    "Prefab/Hall/prefab/MatchPlayerView",
                  ],
                  cc.Prefab,
                  function (e, o, a) {
                    console.log(
                      "completedCount: " +
                        e +
                        "    totalCount: " +
                        o +
                        "   item: " +
                        a
                    ),
                      (t.string = Math.ceil((e / o) * 100) + "%"),
                      (n.fillRange = e / o);
                  },
                  function (t, n) {
                    t ||
                      (console.log("loadRoomPrefablength:   " + n.length),
                      e && e());
                  }
                );
              }),
              (e.prototype.loadHallPrefab = function () {
                var e = this;
                this.isLoadHallPrefab ||
                  cc.loader.loadResDir(
                    "Prefab/Hall/prefab",
                    cc.Prefab,
                    function (t, n) {
                      t ||
                        (console.log("prefablength:   " + n.length),
                        (e.isLoadHallPrefab = !0),
                        cc.director.emit(o.GameEvent.Show_Hall_Icon));
                    }
                  );
              }),
              (e.prototype.loadGamePrefab = function () {
                var e = this;
                this.isLoadGamePrefan ||
                  cc.loader.loadResDir(
                    "Prefab/Hall/prefab",
                    cc.Prefab,
                    function (t, n) {
                      t ||
                        (console.log("prefablength:   " + n.length),
                        (e.isLoadHallPrefab = !0));
                    }
                  );
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = a), cc._RF.pop();
      },
      { "../Enum/GameEnum": "GameEnum" },
    ],
    AudioManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "f74e5Ic6nlLAJEAGpBt3I/l", "AudioManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("./UserInfoManager"),
          a = (function () {
            function e() {
              (this._audioMusicIDs = []),
                (this._audioEffectIDs = []),
                (this._playerAudio = {}),
                (this._palyerId = {}),
                (this._isMusicOpen = !1),
                (this._isEffectOpen = !1);
              var e = o.default.getInstance().getGameSettingInfo();
              (this._isMusicOpen = e.musicStatus),
                (this._isEffectOpen = e.effectStatus);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.playMusicWithPath = function (e, t, n, o) {
                var a = this;
                this.playBGM(e) ||
                  cc.loader.loadRes(e, cc.AudioClip, function (i, r) {
                    i ? cc.log(i.message || i) : a.playMusic(r, e, t, n, o);
                  });
              }),
              (e.prototype.playEffectWithPath = function (e, t, n, o) {
                var a = this;
                cc.loader.loadRes(e, cc.AudioClip, function (i, r) {
                  i ? cc.log(i.message || i) : a.playEffect(r, e, t, n, o);
                });
              }),
              (e.prototype.playMusic = function (e, t, n, o, a) {
                var i = this;
                n || (n = !1), this._isMusicOpen ? o || (o = 1) : (o = 0);
                var r = cc.audioEngine.play(e, n, o);
                this._audioMusicIDs.push(r),
                  (this._playerAudio[t] = e),
                  (this._palyerId[t] = r),
                  cc.audioEngine.setFinishCallback(r, function () {
                    n || i.removeMusicAudioID(r), a && a();
                  });
              }),
              (e.prototype.playEffect = function (e, t, n, o, a) {
                var i = this;
                n || (n = !1), this._isEffectOpen ? o || (o = 1) : (o = 0);
                var r = cc.audioEngine.play(e, n, o);
                return (
                  this._audioEffectIDs.push(r),
                  (this._playerAudio[t] = e),
                  (this._palyerId[t] = r),
                  cc.audioEngine.setFinishCallback(r, function () {
                    n || i.removeEffectAudioID(r), a && a();
                  }),
                  r
                );
              }),
              (e.prototype.playBGM = function (e) {
                if (null != this._palyerId[e]) {
                  var t = this._palyerId[e];
                  return this.resumeAudio(t), !0;
                }
                return !1;
              }),
              (e.prototype.closeAudioEffect = function (e) {
                if (this._palyerId[e]) {
                  var t = this._palyerId[e];
                  this.removeEffectAudioID(t);
                }
              }),
              (e.prototype.pauseAudio = function (e) {
                cc.audioEngine.pause(e);
              }),
              (e.prototype.resumeAudio = function (e) {
                cc.audioEngine.resume(e);
              }),
              (e.prototype.pauseAllAudio = function () {
                cc.audioEngine.pauseAll();
              }),
              (e.prototype.resumeAllAudio = function () {
                cc.audioEngine.resumeAll();
              }),
              (e.prototype.stopMusic = function (e) {
                cc.audioEngine.stop(e), this.removeMusicAudioID(e);
              }),
              (e.prototype.stopEffect = function (e) {
                cc.audioEngine.stop(e), this.removeEffectAudioID(e);
              }),
              (e.prototype.stopAllAudio = function () {
                cc.audioEngine.pauseAll(), (this._audioEffectIDs = []);
              }),
              (e.prototype.stopAllEffect = function () {
                for (var e = 0; e < this._audioEffectIDs.length; e++)
                  this.stopEffect(this._audioEffectIDs[e]);
              }),
              (e.prototype.removeMusicAudioID = function (e) {
                var t = this._audioMusicIDs.indexOf(e);
                -1 != t && this._audioMusicIDs.splice(t);
              }),
              (e.prototype.removeEffectAudioID = function (e) {
                var t = this._audioEffectIDs.indexOf(e);
                -1 != t && this._audioEffectIDs.splice(t);
              }),
              (e.prototype.setMusicOpen = function (e) {
                this._isMusicOpen = e;
                for (
                  var t = this._isMusicOpen ? 1 : 0, n = 0;
                  n < this._audioMusicIDs.length;
                  n++
                )
                  cc.audioEngine.setVolume(this._audioMusicIDs[n], t);
              }),
              (e.prototype.setEffectOpen = function (e) {
                this._isEffectOpen = e;
                for (
                  var t = this._isEffectOpen ? 1 : 0, n = 0;
                  n < this._audioEffectIDs.length;
                  n++
                )
                  cc.audioEngine.setVolume(this._audioEffectIDs[n], t);
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = a), cc._RF.pop();
      },
      { "./UserInfoManager": "UserInfoManager" },
    ],
    BaseComponent: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "3b737pHPwFOap9OGR0TkVxa", "BaseComponent");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Enum/GameEnum"),
          s = e("../Manager/AtlasResManager"),
          c = cc._decorator,
          l = c.ccclass,
          u =
            (c.property,
            (function (e) {
              function t() {
                var t = (null !== e && e.apply(this, arguments)) || this;
                return (
                  (t._eventArray = []),
                  (t._resourcesArray = []),
                  (t._resType = ""),
                  (t._className = "org/cocos2dx/javascript/JSNativeBridge_GP"),
                  (t._noShowBanner = [
                    "taskCell",
                    "AdLoading",
                    "CoinsFlyEffect",
                    "Tips",
                    "DragPropTipsView",
                    "SettlementItem",
                    "ShopSkinPreview",
                    "ShopView",
                    "TimingBoxDealsItem",
                    "TurnHeadPhotoAnim",
                    "CountryItem",
                    "HeadPhotoItem",
                  ]),
                  t
                );
              }
              return (
                a(t, e),
                (t.prototype.start = function () {
                  this.popupAnim();
                }),
                (t.prototype.onDestroy = function () {
                  this.unregisterAllEvents(), this.releaseAllRes();
                }),
                (t.prototype.getEventInfo = function (e) {
                  for (var t = 0; t < this._eventArray.length; t++)
                    if (e == this._eventArray[t].type)
                      return this._eventArray[t];
                }),
                (t.prototype.registerEvent = function (e, t, n, o) {
                  var a = this.getEventInfo(e);
                  if (!a)
                    return (
                      (a = { type: e, callback: t, target: n, useCapture: o }),
                      this._eventArray.push(a),
                      cc.director.on(e, t, n, o)
                    );
                  cc.log(
                    "BaseViewComp::registerEvent error, \u4e8b\u4ef6:" +
                      e +
                      " \u5df2\u6ce8\u518c\uff0c\u8bf7\u52ff\u91cd\u590d\u6ce8\u518c"
                  );
                }),
                (t.prototype.unregisterEvent = function (e) {
                  var t = this.getEventInfo(e);
                  if (t) {
                    cc.director.off(t.type, t.callback, t.target);
                    for (var n = 0; n < this._eventArray.length; n++)
                      if (e == this._eventArray[n].type) {
                        this._eventArray.splice(n, 1);
                        break;
                      }
                  }
                }),
                (t.prototype.registerAllEvents = function () {}),
                (t.prototype.unregisterAllEvents = function () {
                  if (this._eventArray.length > 0) {
                    for (var e = 0; e < this._eventArray.length; e++) {
                      var t = this._eventArray[e];
                      cc.director.off(t.type, t.callback, t.target);
                    }
                    this._eventArray = [];
                  }
                }),
                (t.prototype.popupAnim = function (e) {
                  var t = this.node.scale;
                  (this.node.scale = 0.5),
                    this.node.runAction(
                      cc.sequence(
                        cc.scaleTo(0.15, 1.2 * t),
                        cc.scaleTo(0.1, 1 * t),
                        cc.callFunc(function () {
                          e && e();
                        })
                      )
                    );
                }),
                (t.prototype.closeAnim = function (e) {
                  var t = this.node.scale,
                    n = this.node.getChildByName("node_base");
                  n
                    ? n.runAction(
                        cc.sequence(
                          cc.scaleTo(0.12, 1.2 * t),
                          cc.scaleTo(0.1, 0.5 * t),
                          cc.callFunc(function () {
                            e && e();
                          })
                        )
                      )
                    : e && e();
                }),
                (t.prototype.onClose = function (e) {
                  var t = this;
                  void 0 === e && (e = !0),
                    "boolean" != typeof e && (e = !0),
                    cc.director.emit(r.GameEvent.Play_Close_Audio),
                    e
                      ? this.closeAnim(function () {
                          t.node.destroy();
                        })
                      : this.node.destroy();
                }),
                (t.prototype.isAndroid = function () {
                  return cc.sys.platform == cc.sys.ANDROID;
                }),
                (t.prototype.setRes = function (e) {
                  this._resType = e;
                }),
                (t.prototype.loadRes = function (e, t, n) {
                  if (t == cc.SpriteFrame) {
                    var o = e.split("/"),
                      a = s.default
                        .getInstance()
                        .getSpriteFrame(o[o.length - 1]);
                    a
                      ? n(a)
                      : console.error(
                          "\u52a0\u8f7d\u56fe\u7247\u51fa\u9519\u4e86\uff1a  " +
                            e
                        );
                  } else
                    cc.loader.loadRes(e, t, function (o, a) {
                      if (o)
                        return (
                          console.error(
                            "\u52a0\u8f7d\u51fa\u9519\u4e86\uff1a  " + e
                          ),
                          void cc.log(o.message || o)
                        );
                      var i = e.split("/");
                      t == cc.Prefab && console.log("name: " + i), n(a);
                    });
                }),
                (t.prototype.notShowBanner = function (e) {
                  for (var t in this._noShowBanner)
                    if (this._noShowBanner[t] == e) return !1;
                  return !0;
                }),
                (t.prototype.releaseAllRes = function () {
                  if (this._resourcesArray.length > 0)
                    for (var e = 0; e < this._resourcesArray.length; e++);
                }),
                i([l], t)
              );
            })(cc.Component));
        (n.default = u), cc._RF.pop();
      },
      {
        "../Enum/GameEnum": "GameEnum",
        "../Manager/AtlasResManager": "AtlasResManager",
      },
    ],
    BuriedPointManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "589bfZn921LB6g3xEIeuhFZ", "BuriedPointManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Native/NativeBridge"),
          i = e("../Utils/Utils"),
          r = e("./GameDataManager"),
          s = e("./UserInfoManager"),
          c = (function () {
            function e() {
              this.isBuried = !0;
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.sendBuriedPointInfo = function (e) {
                if (o.ISAPPLET)
                  console.log("buriendName: " + e.event), window.APPLET(e);
                else {
                  if (!e || "object" != typeof e) return;
                  var t = s.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .getUserId(),
                    n = i.default.getCurTimeStamp();
                  (e.ts = n),
                    (e.userId = t),
                    (e.newPlay = r.default.getInstance().getIsNewPlay()),
                    (e.loginDate_ = s.default.getInstance().getLoginDayNum()),
                    (e.numberOfGames_ = s.default.getInstance().getGameCount()),
                    a.default.sendBuriedPointInfo(JSON.stringify(e));
                }
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = c), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
        "./GameDataManager": "GameDataManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    ChessManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "786c8Hre/1MnYqj8YZPfFPd", "ChessManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("./MapGridManager"),
          r = e("./RoomInfoManager"),
          s = e("./UserInfoManager"),
          c = (function () {
            function e() {
              (this._playerChessArray = []), (this._playerChessColors = []);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.addPlayerChess = function (e, t, n, o, a, i) {
                this._playerChessArray[e] || (this._playerChessArray[e] = []),
                  (this._playerChessArray[e][n] = t),
                  t.setChessIndex(n),
                  t.setChessColor(o, a, i),
                  t.setOwnerPlayerIndex(e),
                  t.setRobot(a),
                  t.saveOrigalPosition();
              }),
              (e.prototype.getPlayerChess = function (e, t) {
                return this._playerChessArray[e][t];
              }),
              (e.prototype.getPlayerAllChess = function (e) {
                return this._playerChessArray[e];
              }),
              (e.prototype.disablePlayerAllChesss = function (e) {
                for (
                  var t = this.getPlayerAllChess(e), n = 0;
                  n < t.length;
                  n++
                )
                  t[n].setChessCanClick(!1);
                this.changeMyChessSize(t, !1);
              }),
              (e.prototype.getPlayerCanWalkChess = function (e, t) {
                for (
                  var n = [], o = this.getPlayerAllChess(e), a = 0;
                  a < o.length;
                  a++
                )
                  o[a].canWalk(t) && n.push(o[a]);
                return n;
              }),
              (e.prototype.playChessIsOutBase = function (e) {
                for (
                  var t = this.getPlayerAllChess(e), n = [], o = 0;
                  o < t.length;
                  o++
                )
                  t[o].isArriveTerminalPoint() || n.push(t[o]);
                var a = 0;
                for (o = 0; o < n.length; o++) n[o].isAtTheBase() && (a += 1);
                return a == n.length;
              }),
              (e.prototype.setChessQuickMode = function (e) {
                for (
                  var t = this.getPlayerAllChess(e), n = 0;
                  n < t.length;
                  n++
                )
                  (0 != t[n].getChessIndex() && 1 != t[n].getChessIndex()) ||
                    t[n].setStartPosition();
              }),
              (e.prototype.setPlayerChessToStartPosition = function (e, t) {
                for (
                  var n = this.getPlayerAllChess(e), o = 0;
                  o < n.length;
                  o++
                )
                  o < t && n[o].setStartPosition();
              }),
              (e.prototype.setChessNeareastPos = function (e) {
                for (
                  var t = this.getPlayerAllChess(e), n = 0;
                  n < t.length;
                  n++
                )
                  t[n].setChessNeareastPositon();
              }),
              (e.prototype.setPlayerChessColors = function () {
                for (
                  var e = r.default.getInstance().getChessColor(),
                    t = [],
                    n = [],
                    a = 0;
                  a < o.CHESS_COLOR_COUNT;
                  a++
                )
                  a < e ? t.push(a) : n.push(a);
                this._playerChessColors = n.concat(t);
              }),
              (e.prototype.getPlayerChessColor = function (e) {
                return this._playerChessColors[e];
              }),
              (e.prototype.getCanUseBombChess = function () {
                for (
                  var e = s.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .getPlayerIndex(),
                    t = this.getPlayerAllChess(e),
                    n = [],
                    o = 0;
                  o < t.length;
                  o++
                ) {
                  var a = t[o],
                    i = a.getCurPosGrid();
                  a.isAtTheBase() ||
                    a.isArriveTerminalPoint() ||
                    i.isSafe() ||
                    i.hasBomb() ||
                    n.push(a);
                }
                return n;
              }),
              (e.prototype.getCanUseProtectiveChess = function () {
                for (
                  var e = s.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .getPlayerIndex(),
                    t = this.getPlayerAllChess(e),
                    n = [],
                    o = 0;
                  o < t.length;
                  o++
                ) {
                  var a = t[o];
                  a.isAtTheBase() ||
                    a.isArriveTerminalPoint() ||
                    a.hasProtectiveCover() ||
                    n.push(a);
                }
                return n;
              }),
              (e.prototype.checkBombUseSuccess = function (e) {
                e.x += 12;
                for (
                  var t = s.default.getInstance().getMyselfUserInfo(),
                    n = i.default
                      .getInstance()
                      .getPlayerPathInfo(t.getPlayerIndex()),
                    o = !1,
                    a = [],
                    r = 0;
                  r < n.normal.length;
                  r++
                )
                  (c = i.default
                    .getInstance()
                    .getMapGrid(n.normal[r])).isEmptyGrid() && a.push(c);
                for (r = 0; r < a.length; r++) {
                  var c;
                  if ((c = a[r]).isTouchPointInGrid(e)) {
                    (o = !0), c.setBomb(!0);
                    break;
                  }
                }
                return o;
              }),
              (e.prototype.checkProtectiveUseSuccess = function (e) {
                for (
                  var t = s.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .getPlayerIndex(),
                    n = !1,
                    o = [],
                    a = this.getPlayerAllChess(t),
                    i = 0;
                  i < a.length;
                  i++
                )
                  a[i].isAtTheBase() ||
                    a[i].isArriveTerminalPoint() ||
                    o.push(a[i]);
                for (i = 0; i < o.length; i++)
                  if (
                    o[i].isTouchPointInChess(e) &&
                    !o[i].hasProtectiveCover()
                  ) {
                    (n = !0), o[i].setProtectiveCover(!0);
                    break;
                  }
                return n;
              }),
              (e.prototype.getAllChessInGrid = function () {
                var e = s.default.getInstance().getAllUser();
                r.default.getInstance().getGameMode() == a.GameMode.Local &&
                  (e = s.default.getInstance().getLocalAllUser());
                for (var t = [], n = 0; n < e.length; n++)
                  for (
                    var o = this.getPlayerAllChess(e[n].getPlayerIndex()),
                      i = 0;
                    i < o.length;
                    i++
                  )
                    o[i].isAtTheBase() || t.push(o[i]);
                return t;
              }),
              (e.prototype.sortAllChessZIndex = function () {
                var e = this.getAllChessInGrid(),
                  t = 1;
                e.sort(function (e, t) {
                  return t.getPosition().y - e.getPosition().y;
                });
                for (
                  var n = [],
                    o = function (e) {
                      for (var t = 0; t < n.length; t++) {
                        var o = n[t];
                        if (o[0].checkIsSameRow(e)) return o.push(e), !0;
                      }
                      return !1;
                    },
                    a = 0;
                  a < e.length;
                  a++
                )
                  o(e[a]) || ((i = []).push(e[a]), n.push(i));
                for (a = 0; a < n.length; a++)
                  n[a].sort(function (e, t) {
                    return e.getPosition().x - t.getPosition().x;
                  });
                for (a = 0; a < n.length; a++)
                  for (var i = n[a], r = 0; r < i.length; r++)
                    i[r].setZIndex(t), (t += 1);
              }),
              (e.prototype.getInNormalLineChess = function (e) {
                for (
                  var t = [], n = this.getPlayerAllChess(e), o = 0;
                  o < n.length;
                  o++
                )
                  n[o].isInNormalLine() && t.push(n[o]);
                return t;
              }),
              (e.prototype.changeMyChessSize = function (e, t) {
                for (var n = 0; n < e.length; n++) {
                  var o = e[n];
                  if (
                    !o.isAtTheBase() &&
                    !o.isArriveTerminalPoint() &&
                    o.getCurPosGrid().getAllChess().length > 1
                  )
                    for (
                      var a = o.getCurPosGrid().getMyselfChess(), i = 0;
                      i < a.length;
                      i++
                    )
                      t ? a[i].setMiddleSize() : a[i].setSmallerSize();
                }
              }),
              (e.prototype.hasChessInVerticalLine = function (e) {
                for (
                  var t = this.getPlayerAllChess(e), n = 0;
                  n < t.length;
                  n++
                )
                  if (t[n].isInVerticalLine()) return !0;
                return !1;
              }),
              (e.prototype.getEndPos = function (e) {
                for (
                  var t = 99, n = this.getPlayerAllChess(e), o = 0;
                  o < n.length;
                  o++
                )
                  n[o].getDiffStepsToTerminal() < t &&
                    0 != n[o].getDiffStepsToTerminal() &&
                    (t = n[o].getDiffStepsToTerminal());
                return (
                  console.log(
                    "\u8ddd\u79bb\u7ec8\u70b9\u8fd8\u5dee\uff1a  " +
                      t +
                      "\u6b65"
                  ),
                  t
                );
              }),
              (e.prototype.delectChess = function (e) {
                var t = this._playerChessArray[e];
                if (t.length)
                  for (var n = 0; n < t.length; n++) t[n].hideChess();
              }),
              (e.prototype.addChess = function (e, t, n) {
                var o = this._playerChessArray[e][t];
                o && (o.setChessInBase(n), o.setRobot(!1), o.setOriginalSize());
              }),
              (e.prototype.clearData = function () {
                (this._playerChessArray = []), (this._playerChessColors = []);
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = c), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "./MapGridManager": "MapGridManager",
        "./RoomInfoManager": "RoomInfoManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    Chess: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "894d3ZCyJFP3b4CqR0seABa", "Chess");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/ChessManager"),
          p = e("../Framework/Manager/GameDataManager"),
          f = e("../Framework/Manager/LuckManager"),
          h = e("../Framework/Manager/MapGridManager"),
          g = e("../Framework/Manager/UserInfoManager"),
          m = e("../Framework/Utils/Utils"),
          _ = e("../Framework/Manager/TaskManager"),
          y = e("../Framework/Manager/RoomInfoManager"),
          v = e("../Framework/Manager/RobotManager"),
          I = cc._decorator,
          C = I.ccclass,
          k = I.property,
          w = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprChess = null),
                (t.nodeClick = null),
                (t.sprCircle = null),
                (t.spfChessColors = []),
                (t.sprBomb = null),
                (t.labDiffSteps = null),
                (t._chessIndex = 0),
                (t._isSafeStatus = !0),
                (t._ownerPlayerIndex = c.PlayerIndex.LeftBottom),
                (t._curPosIndex = -1),
                (t._walkActionIndex = 0),
                (t._beEatenActionIndex = 0),
                (t._orginalPos = null),
                (t._isArriveTerminalPoint = !1),
                (t._orgianlScale = 0),
                (t._hasProtectiveCover = !1),
                (t._protectiveAppearAnim = null),
                (t._protectiveDisappearAnim = null),
                (t._protectiveAnimAppearName = "protective_appear"),
                (t._protectiveAnimDisappearName = "protective_disappear"),
                (t._isRobot = !1),
                (t._walkSteps = 0),
                (t._firstInVerticalLine = !0),
                (t._colorList = ["lan", "hong", "lv", "huang"]),
                (t._showSafe = !0),
                t
              );
            }
            var n;
            return (
              a(t, e),
              (n = t),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  (this._orgianlScale = this.node.scale);
              }),
              (t.prototype.onTouchMove = function (e) {
                var t = e.getLocation(),
                  n = this.node.parent.convertToNodeSpaceAR(t);
                (this.node.x = n.x), (this.node.y = n.y);
              }),
              (t.prototype.onTouchEnd = function (e) {
                var t = this.getCurPosGrid();
                null != t && t.leaveGrid(this),
                  g.default.getInstance().getMyselfUserInfo();
                for (
                  var n = h.default
                      .getInstance()
                      .getPlayerPathInfo(this._ownerPlayerIndex),
                    o = [],
                    a = 0;
                  a < n.terminal.length;
                  a++
                ) {
                  var i = h.default.getInstance().getMapGrid(n.terminal[a]);
                  o.push(i);
                }
                var r = n.terminal[n.terminal.length - 1];
                for (a = 0; a < o.length; a++)
                  if ((i = o[a]).isTouchPointInGrid(e.getLocation())) {
                    (this.node.position = i.node.position),
                      i.enterGrid(this),
                      (this._curPosIndex = i.getGridIndex()),
                      this.checkArriveTerminalPoint(r);
                    break;
                  }
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Player_Operation_OutTime,
                  this.onOutTime,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Guide_Select_Chess,
                    this.guideChess,
                    this
                  );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.guideChess = function (e) {
                e.playerIndex == this._ownerPlayerIndex &&
                  e.chessIndex == this._chessIndex &&
                  this.onClickChess();
              }),
              (t.prototype.setChessIndex = function (e) {
                this._chessIndex = e;
              }),
              (t.prototype.getChessIndex = function () {
                return this._chessIndex;
              }),
              (t.prototype.setSafeStatus = function (e) {
                this._isSafeStatus = e;
              }),
              (t.prototype.isInSafaStatus = function () {
                return this._isSafeStatus;
              }),
              (t.prototype.setOwnerPlayerIndex = function (e) {
                this._ownerPlayerIndex = e;
              }),
              (t.prototype.getOwnerPlayerIndex = function () {
                return this._ownerPlayerIndex;
              }),
              (t.prototype.setChessColor = function (e, t, n) {
                var o;
                (o =
                  s.SKIN_PICTURE_PATH + n + "_img_chess_" + this._colorList[e]),
                  this.setSpfsRes(this.sprChess, o);
              }),
              (t.prototype.setSpfsRes = function (e, t) {
                this.loadRes(t, cc.SpriteFrame, function (t) {
                  e.spriteFrame = t;
                });
              }),
              (t.prototype.isAtTheBase = function () {
                return -1 == this._curPosIndex;
              }),
              (t.prototype.getWalkPathIndexArray = function (e) {
                var t = [],
                  n = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex),
                  o = h.default
                    .getInstance()
                    .getBarrierStatus(this._ownerPlayerIndex);
                if (this.isAtTheBase())
                  for (var a = n.normal[0], i = a, r = a; r <= i; r++)
                    t.push(r);
                else {
                  var c = null,
                    l = (c = o ? n.normal : n.terminal).indexOf(
                      this._curPosIndex
                    );
                  if (l != s.ARRAY_ELE_NOT_EXIST) {
                    var u = l;
                    for (r = 1; r <= e; r++)
                      (u += 1) == c.length && (u = 0), t.push(c[u]);
                  }
                }
                return t;
              }),
              (t.prototype.canArriveTerminal = function (e) {
                if (this.isAtTheBase() || this.isArriveTerminalPoint())
                  return !1;
                var t = h.default
                  .getInstance()
                  .getPlayerPathInfo(this._ownerPlayerIndex);
                if (
                  h.default
                    .getInstance()
                    .getBarrierStatus(this._ownerPlayerIndex)
                )
                  return !1;
                var n = 0,
                  o = t.terminal,
                  a = o.indexOf(this._curPosIndex);
                if (a == s.ARRAY_ELE_NOT_EXIST) return !1;
                for (var i = 0; i < o.length; i++) i > a && (n += 1);
                return e == n;
              }),
              (t.prototype.canWalk = function (e) {
                if (this.isArriveTerminalPoint()) return !1;
                var t = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex),
                  n = h.default
                    .getInstance()
                    .getBarrierStatus(this._ownerPlayerIndex);
                if ((this.isMyselfChess(), this.isAtTheBase()))
                  return e == s.DICE_MAX_POINTS;
                if (n) return !0;
                var o = 0,
                  a = t.terminal,
                  i = a.indexOf(this._curPosIndex);
                if (i == s.ARRAY_ELE_NOT_EXIST)
                  return (
                    cc.log(
                      "Chess::canWalk error, this._curPosIndex:" +
                        this._curPosIndex +
                        " not exist"
                    ),
                    !1
                  );
                for (var r = 0; r < a.length; r++) r > i && (o += 1);
                return e < o || e == o;
              }),
              (t.prototype.walk = function (e, t) {
                var n = this;
                l.default
                  .getInstance()
                  .closeAudioEffect(c.AudioType.Player_Opt_CD),
                  this.hideBombIcon();
                var o = h.default
                  .getInstance()
                  .getPlayerPathInfo(this._ownerPlayerIndex);
                this.isAtTheBase() || this.getCurPosGrid().leaveGrid(this),
                  this._curPosIndex;
                var a = this.getWalkPathIndexArray(e),
                  i = h.default.getInstance().getWalkPathMapGrids(a);
                this.setWalkSteps(this.getWalkSteps() + i.length),
                  (this._walkActionIndex = 0);
                var r = o.terminal[o.terminal.length - 1];
                (this.node.zIndex = 100),
                  this.playWalkAnim(i, function () {
                    var e = i[i.length - 1],
                      o = function (o) {
                        if (
                          (void 0 === o && (o = !1),
                          e.enterGrid(n),
                          (n._curPosIndex = e.getGridIndex()),
                          n.checkArriveTerminalPoint(r),
                          e.isRocket())
                        )
                          l.default
                            .getInstance()
                            .playEffectWithPath(c.AudioType.Rocket_Speed_Up),
                            n.walk(3, t);
                        else if (e.isSafe()) {
                          var a = h.default
                            .getInstance()
                            .getPlayerPathInfo(n._ownerPlayerIndex);
                          if (
                            n.isMyselfChess() &&
                            1 == g.default.getInstance().getGameTotalRounds() &&
                            a.normal[0] != n._curPosIndex &&
                            p.default.getInstance().getIsSafe()
                          ) {
                            var i = {
                              ownerPlayerIndex: n._ownerPlayerIndex,
                              isEatOther: o,
                              isArriveTerminalPoint: n._isArriveTerminalPoint,
                            };
                            p.default.getInstance().setIsSafe(!1),
                              cc.director.emit(c.GameEvent.Show_Guide_Safe, i);
                          } else
                            cc.director.emit(
                              c.GameEvent.Player_Operation_Completed,
                              n._ownerPlayerIndex,
                              o,
                              n._isArriveTerminalPoint
                            );
                        } else
                          e.hasBomb()
                            ? (e.setBomb(!1),
                              l.default
                                .getInstance()
                                .playEffectWithPath(c.AudioType.Bomb),
                              n.hasProtectiveCover()
                                ? (n.setProtectiveCover(!1),
                                  t && t(),
                                  cc.director.emit(
                                    c.GameEvent.Player_Operation_Completed,
                                    n._ownerPlayerIndex,
                                    o,
                                    n._isArriveTerminalPoint
                                  ),
                                  n.isMyselfChess())
                                : ((n.node.active = !1),
                                  e.leaveGrid(n),
                                  e.playBombEff(function () {
                                    (n.node.active = !0),
                                      n.playBombBackAnim(0, function () {
                                        (n._curPosIndex = -1),
                                          d.default
                                            .getInstance()
                                            .sortAllChessZIndex(),
                                          t && t(),
                                          cc.director.emit(
                                            c.GameEvent
                                              .Player_Operation_Completed,
                                            n._ownerPlayerIndex,
                                            o,
                                            n._isArriveTerminalPoint
                                          ),
                                          n.isMyselfChess();
                                      });
                                  })))
                            : e.hasRoadblock()
                            ? ((n.node.active = !1),
                              e.playroadblock(function () {
                                (n.node.active = !0),
                                  d.default.getInstance().sortAllChessZIndex(),
                                  t && t(),
                                  cc.director.emit(
                                    c.GameEvent.Player_Operation_Completed,
                                    n._ownerPlayerIndex,
                                    o,
                                    n._isArriveTerminalPoint
                                  );
                              }))
                            : (d.default.getInstance().sortAllChessZIndex(),
                              t && t(),
                              cc.director.emit(
                                c.GameEvent.Player_Operation_Completed,
                                n._ownerPlayerIndex,
                                o,
                                n._isArriveTerminalPoint
                              ),
                              n.isMyselfChess());
                        n.isInVerticalLine() &&
                          n._firstInVerticalLine &&
                          (n.isMyselfChess()
                            ? v.default.getInstance().playChessInVerticalLine()
                            : v.default
                                .getInstance()
                                .robotChessInVerticalLine(n._ownerPlayerIndex),
                          (n._firstInVerticalLine = !1));
                      };
                    if (e.isSafe())
                      l.default
                        .getInstance()
                        .playEffectWithPath(c.AudioType.Chess_Arrive_Safe);
                    else {
                      var a = e.getBeEatenChess(n);
                      if (a)
                        return void (a.hasProtectiveCover()
                          ? (a.setProtectiveCover(!1), o())
                          : (n.isMyselfChess() &&
                              u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedPointKey.Chess,
                                  isBeEaten: !1,
                                  isEateOther: !0,
                                }),
                            n.eatenOtherChess(a.getOwnerPlayerIndex()),
                            y.default.getInstance().getGameMode() !=
                              c.GameMode.Local &&
                              f.default
                                .getInstance()
                                .changeLuck(
                                  n._ownerPlayerIndex,
                                  c.LuckChangeType.Eate
                                ),
                            l.default
                              .getInstance()
                              .playEffectWithPath(c.AudioType.Chess_Be_Eaten),
                            a.beEaten(n._ownerPlayerIndex, function () {
                              h.default
                                .getInstance()
                                .getBarrierStatus(n._ownerPlayerIndex) &&
                                (cc.director.emit(
                                  c.GameEvent.Remove_Barrier,
                                  n._ownerPlayerIndex
                                ),
                                h.default
                                  .getInstance()
                                  .setBarrierStatus(n._ownerPlayerIndex, !1)),
                                o(!0);
                            })));
                    }
                    o();
                  }),
                  cc.director.emit(
                    c.GameEvent.Player_Walk_Start,
                    this._ownerPlayerIndex
                  );
              }),
              (t.prototype.eatenOtherChess = function (e) {
                if (
                  (console.log(
                    "\u6211\u5403\u522b\u4eba\u7684\u68cb\u5b50\uff1a " +
                      this.getChessIndex()
                  ),
                  cc.director.emit(c.GameEvent.eatChess),
                  this.isMyselfChess())
                ) {
                  p.default.getInstance().setEatOther();
                  var t = m.default.getRandomNum(3, 6);
                  this.scheduleOnce(function () {
                    v.default.getInstance().beEatSendExpression(e);
                  }, t);
                }
              }),
              (t.prototype.beEatenEff = function () {
                if (
                  (console.log(
                    "\u6211\u88ab\u522b\u4eba\u7684\u68cb\u5b50\u5403\u4e86\uff1a " +
                      this.getChessIndex()
                  ),
                  cc.director.emit(c.GameEvent.eatChess),
                  !this.isMyselfChess())
                ) {
                  p.default.getInstance().setMyBeEatenOther();
                  var e = m.default.getRandomNum(3, 6);
                  this.scheduleOnce(function () {}, e);
                }
              }),
              (t.prototype.playWalkAnim = function (e, t) {
                var n = this,
                  o = e[this._walkActionIndex];
                if (null == o)
                  return (
                    console.log("grids:  " + e),
                    console.log(
                      "this._walkActionIndex:  " + this._walkActionIndex
                    ),
                    (this._walkActionIndex = 0),
                    void t()
                  );
                var a = o.node;
                this.node.runAction(
                  cc.sequence(
                    cc.spawn(
                      cc.moveTo(0.2, cc.v2(a.x, a.y)),
                      cc.sequence(
                        cc.scaleTo(0.1, 1.8 * this._orgianlScale),
                        cc.scaleTo(0.1, this._orgianlScale)
                      )
                    ),
                    cc.callFunc(function () {
                      o.playGreenCircleAnim(),
                        n._walkActionIndex == e.length - 1
                          ? ((n._walkActionIndex = 0),
                            cc.director.emit(c.GameEvent.Close_Guide_Ui),
                            n.node.resumeAllActions(),
                            t())
                          : ((n._walkActionIndex += 1),
                            n.node.runAction(
                              cc.sequence(
                                cc.delayTime(0.1),
                                cc.callFunc(function () {
                                  n.playWalkAnim(e, t);
                                })
                              )
                            ));
                    })
                  )
                ),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Chess_Walk);
              }),
              (t.prototype.saveOrigalPosition = function () {
                this._orginalPos = this.node.position;
              }),
              (t.prototype.getRetreatPathIndexArray = function () {
                var e = [],
                  t = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex).normal,
                  n = t.indexOf(this._curPosIndex);
                if (n != s.ARRAY_ELE_NOT_EXIST)
                  for (var o = t.length - 1; o >= 0; o--) o < n && e.push(t[o]);
                return e;
              }),
              (t.prototype.isMyselfChess = function () {
                var e = g.default
                  .getInstance()
                  .getMyselfUserInfo()
                  .getPlayerIndex();
                return this._ownerPlayerIndex == e;
              }),
              (t.prototype.beEaten = function (e, t) {
                this.isMyselfChess() &&
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.Chess,
                      isBeEaten: !0,
                      isEateOther: !1,
                    }),
                  y.default.getInstance().getGameMode() != c.GameMode.Local &&
                    f.default
                      .getInstance()
                      .changeLuck(
                        this._ownerPlayerIndex,
                        c.LuckChangeType.beEaten
                      );
                for (
                  var n = this.getRetreatPathIndexArray(),
                    o = h.default.getInstance().getWalkPathMapGrids(n),
                    a = [],
                    i = 0;
                  i < o.length;
                  i++
                ) {
                  var r = o[i].node;
                  a.push(r.position);
                }
                a.push(this._orginalPos),
                  (this._beEatenActionIndex = 0),
                  this.playBeEatenAnim(a, e, t);
                var s = this.getCurPosGrid();
                s && s.leaveGrid(this),
                  (this._curPosIndex = -1),
                  this.setWalkSteps(0);
              }),
              (t.prototype.playBeEatenAnim = function (e, t, n) {
                var o,
                  a = this,
                  i = e[this._beEatenActionIndex],
                  r = 0;
                this._beEatenActionIndex == e.length - 1
                  ? ((r = 0.1),
                    (o = cc.moveTo(r, cc.v2(i.x, i.y)).easing(cc.easeOut(3))))
                  : ((r = 0.03), (o = cc.moveTo(r, cc.v2(i.x, i.y)))),
                  this.node.runAction(
                    cc.sequence(
                      o,
                      cc.callFunc(function () {
                        a._beEatenActionIndex == e.length - 1
                          ? ((a._beEatenActionIndex = 0),
                            n && n(),
                            a.beEatenEff(t))
                          : ((a._beEatenActionIndex += 1),
                            a.playBeEatenAnim(e, t, n));
                      })
                    )
                  );
              }),
              (t.prototype.checkArriveTerminalPoint = function (e) {
                if (
                  ((this._isArriveTerminalPoint = this._curPosIndex == e),
                  this._isArriveTerminalPoint)
                ) {
                  for (
                    var t = d.default
                        .getInstance()
                        .getPlayerAllChess(this._ownerPlayerIndex),
                      n = 0;
                    n < t.length;
                    n++
                  )
                    t[n].isArriveTerminalPoint();
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Chess_Arrive_Terminal),
                    this.isMyselfChess() &&
                      _.default
                        .getInstance()
                        .setTaskProgress(c.TaskType.Task_end_point);
                }
              }),
              (t.prototype.isArriveTerminalPoint = function () {
                return this._isArriveTerminalPoint;
              }),
              (t.prototype.onClickChess = function () {
                l.default.getInstance().stopAllEffect(),
                  d.default
                    .getInstance()
                    .disablePlayerAllChesss(this._ownerPlayerIndex);
                var e = p.default.getInstance().getDicePoints();
                this.walk(e);
              }),
              (t.prototype.setChessCanClick = function (e) {
                var t;
                if (e)
                  if ((t = this.getCurPosGrid())) {
                    var n = t.getAllChess();
                    1 == n.length && n[0].isMyselfChess(),
                      (this.nodeClick.active = !0);
                  } else this.nodeClick.active = !0;
                else
                  (this.nodeClick.active = !1),
                    (t = this.getCurPosGrid()) && t.disableClick();
                (this.sprCircle.active = e), (this.sprCircle.rotation = 0);
              }),
              (t.prototype.setSmallerSize = function () {
                this.node.scale = 0.5 * this._orgianlScale;
              }),
              (t.prototype.setMiddleSize = function () {
                this.node.scale = 0.75 * this._orgianlScale;
              }),
              (t.prototype.setOriginalSize = function () {
                this.node.scale = 1 * this._orgianlScale;
              }),
              (t.prototype.setStartPosition = function () {
                var e = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex),
                  t = h.default.getInstance().getMapGrid(e.normal[0]),
                  n = t.node;
                (this.node.position = n.position),
                  t.enterGrid(this),
                  (this._curPosIndex = e.normal[0]);
              }),
              (t.prototype.setChessNeareastPositon = function () {
                var e = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex),
                  t = e.terminal[e.terminal.length - 2],
                  n = h.default.getInstance().getMapGrid(t),
                  o = n.node;
                (this.node.position = o.position),
                  n.enterGrid(this),
                  (this._curPosIndex = t);
              }),
              (t.prototype.setChessInBase = function (e) {
                (this.node.active = !0),
                  (this._curPosIndex = -1),
                  (this.node.position = e);
              }),
              (t.prototype.onOutTime = function () {
                this.isMyselfChess() && this.setChessCanClick(!1);
              }),
              (t.prototype.hideChess = function () {
                this.node.active = !1;
              }),
              (t.prototype.hasProtectiveCover = function () {
                return this._hasProtectiveCover;
              }),
              (t.prototype.setProtectiveCover = function () {}),
              (t.prototype.playBombBackAnim = function (e, t) {
                var n = this,
                  o = [],
                  a = h.default
                    .getInstance()
                    .getPlayerPathInfo(this._ownerPlayerIndex).normal,
                  i = (a[e], a.indexOf(this._curPosIndex));
                if (i != s.ARRAY_ELE_NOT_EXIST)
                  for (var r = i; r < a.length && r >= 0; r--) o.push(a[r]);
                if (o.length > 0) {
                  var c = h.default.getInstance().getWalkPathMapGrids(o),
                    l = [];
                  for (r = 0; r < c.length; r++) {
                    var u = c[r].node;
                    l.push(u.position);
                  }
                  l.push(this._orginalPos), this.setWalkSteps(0);
                  var d = this.getCurPosGrid();
                  d && d.leaveGrid(this);
                  var p = 0,
                    f = function () {
                      var e = l[p];
                      n.node.runAction(
                        cc.sequence(
                          cc.moveTo(0.1, cc.v2(e.x, e.y)),
                          cc.callFunc(function () {
                            p == l.length - 1
                              ? ((p = 0), t && t())
                              : ((p += 1), f());
                          })
                        )
                      );
                    };
                  f();
                }
              }),
              (t.prototype.getCurPosGrid = function () {
                return this.isAtTheBase()
                  ? null
                  : h.default.getInstance().getMapGrid(this._curPosIndex);
              }),
              (t.prototype.isTouchPointInChess = function (e) {
                var t = this.node.getBoundingBox(),
                  n = this.node.parent.convertToNodeSpaceAR(e);
                return t.contains(n);
              }),
              (t.prototype.setZIndex = function (e) {
                this.node.zIndex = e;
              }),
              (t.prototype.getPosition = function () {
                return this.node.position;
              }),
              (t.prototype.checkIsSameRow = function (e) {
                var t = e.getPosition();
                return Math.abs(Math.floor(t.y - this.node.position.y)) < 2;
              }),
              (t.prototype.getProtectiveWorldPosition = function () {
                return m.default.getWorldPosition(this.node);
              }),
              (t.prototype.showBombIcon = function (e) {
                (this.sprBomb.active = !0),
                  (this.sprBomb.position = this.node.convertToNodeSpaceAR(e));
              }),
              (t.prototype.hideBombIcon = function () {
                this.sprBomb.active = !1;
              }),
              (t.prototype.setRobot = function (e) {
                this._isRobot = e;
              }),
              (t.prototype.isRobot = function () {
                return this._isRobot;
              }),
              (t.prototype.getDiffStepsToTerminal = function () {
                var e = h.default
                  .getInstance()
                  .getPlayerPathInfo(this._ownerPlayerIndex);
                if (this.isAtTheBase()) return e.terminal.length;
                if (this._curPosIndex == e.normal[e.normal.length - 1])
                  return e.terminal.length;
                var t = e.terminal.indexOf(this._curPosIndex);
                return e.terminal.length - 1 - t;
              }),
              (t.prototype.getArriveGrid = function (e) {
                var t = this.getWalkPathIndexArray(e),
                  n = h.default.getInstance().getWalkPathMapGrids(t);
                return n[n.length - 1];
              }),
              (t.prototype.canWalkToSafeGrid = function (e) {
                return this.getArriveGrid(e).isSafe();
              }),
              (t.prototype.canWalkToPropGrid = function (e) {
                return this.getArriveGrid(e).isRocket();
              }),
              (t.prototype.canWalkToBombGrid = function (e) {
                return this.getArriveGrid(e).hasBomb();
              }),
              (t.prototype.canEateOther = function (e) {
                var t = this.getArriveGrid(e);
                if (t) {
                  if (t && t.isSafe()) return null;
                  var n = t.getBeEatenChess(this);
                  return n && !n.hasProtectiveCover() ? n : null;
                }
                return null;
              }),
              (t.prototype.setNodeClickScale = function (e) {
                this.nodeClick.scale = e ? 1.5 : 1;
              }),
              (t.prototype.getCurrentPosIndex = function () {
                return this._curPosIndex;
              }),
              (t.prototype.isInNormalLine = function () {
                return h.default
                  .getInstance()
                  .isInNormalLine(this._curPosIndex);
              }),
              (t.prototype.isInVerticalLine = function () {
                return (
                  h.default
                    .getInstance()
                    .getVerticalLine(this._ownerPlayerIndex)
                    .indexOf(this._curPosIndex) != s.ARRAY_ELE_NOT_EXIST
                );
              }),
              (t.prototype.getDiffStepsToDestination = function (e) {
                var t;
                t = e instanceof n ? e.getCurrentPosIndex() : e.getGridIndex();
                for (
                  var o = h.default.getInstance().getPlayerPathInfo(0),
                    a = 0,
                    i = o.normal.indexOf(this._curPosIndex);
                  o.normal[i] != t;

                )
                  (i += 1) > o.normal.length - 1 && (i = 0), (a += 1);
                return a;
              }),
              (t.prototype.isInAttackRange = function (e) {
                if (!e.isInNormalLine()) return !1;
                var t = this.getDiffStepsToDestination(e);
                return t >= 1 && t <= 6;
              }),
              (t.prototype.setWalkSteps = function (e) {
                this._walkSteps = e;
              }),
              (t.prototype.getWalkSteps = function () {
                return this._walkSteps;
              }),
              i([k(cc.Sprite)], t.prototype, "sprChess", void 0),
              i([k(cc.Node)], t.prototype, "nodeClick", void 0),
              i([k(cc.Node)], t.prototype, "sprCircle", void 0),
              i([k(cc.SpriteFrame)], t.prototype, "spfChessColors", void 0),
              i([k(cc.Node)], t.prototype, "sprBomb", void 0),
              i([k(cc.Label)], t.prototype, "labDiffSteps", void 0),
              (n = i([C], t))
            );
          })(r.default);
        (n.default = w), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/ChessManager": "ChessManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/LuckManager": "LuckManager",
        "../Framework/Manager/MapGridManager": "MapGridManager",
        "../Framework/Manager/RobotManager": "RobotManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/TaskManager": "TaskManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    CirculateManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "4865dK9+s1HDa14HAadca1a", "CirculateManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameEnum"),
          a = e("../Native/NativeBridge"),
          i = e("../Utils/Utils"),
          r = e("./GameDataManager"),
          s = (function () {
            function e() {
              (this.activityWinCount = {}),
                (this.isActivitying = !1),
                (this.rankIndex = 16),
                (this.lostCount = 0),
                (this.isPlayAgain = !1),
                (this.isPlayMatch = !1),
                (this.competitionList = []),
                (this.competitionCount = 0),
                (this.First = !1),
                (this.isGameover = !1),
                (this.gameMode = o.GameMode.BombItem),
                (this.circulateActivity = o.circulateActivity.cup);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.getActivityList = function () {
                for (
                  var e = [],
                    t = r.default.getInstance().getTools().getCupActivity(),
                    n = 0;
                  n < t.info.length;
                  n++
                ) {
                  var a = t.info[n];
                  a.activityState != o.activityState.delete && e.push(a);
                }
                return e;
              }),
              (e.prototype.getActivityData = function () {
                for (
                  var e = null,
                    t = r.default.getInstance().getTools().getCupActivity(),
                    n = 0;
                  n < t.info.length;
                  n++
                ) {
                  var a = t.info[n];
                  a.activityState != o.activityState.delete && (e = a);
                }
                return e;
              }),
              (e.prototype.getActivityState = function (e) {
                var t = i.default.getWeekDate(),
                  n = this.activityOpenDay(
                    e.startDay,
                    e.sustainTime,
                    e.startTime
                  );
                if (-1 != n.indexOf(t)) {
                  var a = i.default.getHours();
                  0 == n.indexOf(t)
                    ? e.startTime <= a
                      ? o.activityState.progress
                      : o.activityState.today
                    : n.indexOf(t) == n.length - 1 && e.startTime < a
                    ? o.activityState.today
                    : o.activityState.progress;
                } else o.activityState.today;
                return o.activityState.progress;
              }),
              (e.prototype.activityOpenDay = function (e, t, n) {
                var o = t / 24,
                  a = [];
                0 != n && a.push(e);
                for (var i = 1; i <= o; i++)
                  e + i > 6 ? a.push(e + i - 6) : a.push(e + i);
                return a;
              }),
              (e.prototype.addActivityCount = function (e) {
                var t = !1;
                for (var n in this.activityWinCount)
                  if (this.activityWinCount[n].type == e) {
                    this.activityWinCount[n].count++, (t = !0);
                    break;
                  }
                if (!t) {
                  var i = { type: e, count: 1 };
                  this.activityWinCount[e] = i;
                }
                a.default.saveData(
                  o.DataSaveKey.activityWinCount,
                  JSON.stringify(this.activityWinCount)
                );
              }),
              (e.prototype.getActivityCount = function (e) {
                var t = 0;
                for (var n in this.activityWinCount)
                  if (this.activityWinCount[n].type == e) {
                    t = this.activityWinCount[n].count;
                    break;
                  }
                return t;
              }),
              (e.prototype.setRankIndex = function (e, t) {
                var n = [];
                1 == this.competitionCount
                  ? ((this.First = e),
                    e
                      ? (this.rankIndex = 8)
                      : ((n = i.default.getRandomArrayElements(
                          [9, 10, 11, 12, 13, 14, 15, 16],
                          1
                        )),
                        (this.rankIndex = n[0])))
                  : 2 == this.competitionCount
                  ? this.First
                    ? e
                      ? (this.rankIndex = 4)
                      : ((n = i.default.getRandomArrayElements(
                          [5, 6, 7, 8],
                          1
                        )),
                        (this.rankIndex = n[0]))
                    : e
                    ? ((n = i.default.getRandomArrayElements([5, 6, 7, 8], 1)),
                      (this.rankIndex = n[0]))
                    : ((this.First = !1),
                      (n = i.default.getRandomArrayElements(
                        [9, 10, 11, 12, 13, 14, 15, 16],
                        1
                      )),
                      (this.rankIndex = n[0]))
                  : 3 == this.competitionCount
                  ? e &&
                    (this.First
                      ? 3 == i.default.countNum(this.competitionList, 1)
                        ? ((this.rankIndex = t), (this.isGameover = !0))
                        : 2 == i.default.countNum(this.competitionList, 1) &&
                          ((n = i.default.getRandomArrayElements(
                            [5, 6, 7, 8],
                            1
                          )),
                          (this.rankIndex = n[0]))
                      : ((this.First = !1),
                        (n = i.default.getRandomArrayElements([5, 6, 7, 8], 1)),
                        (this.rankIndex = n[0])))
                  : 4 == this.competitionCount
                  ? e
                    ? ((n = i.default.getRandomArrayElements([1, 2, 3, 4], 1)),
                      (this.rankIndex = n[0]))
                    : ((this.First = !1),
                      (n = i.default.getRandomArrayElements([5, 6, 7, 8], 1)),
                      (this.rankIndex = n[0]))
                  : 5 == this.competitionCount &&
                    ((this.rankIndex = t), (this.isGameover = !0));
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = s), cc._RF.pop();
      },
      {
        "../Enum/GameEnum": "GameEnum",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
        "./GameDataManager": "GameDataManager",
      },
    ],
    CoinsFlyEffect: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "977472v/lVDEoAtm0D1alg9", "CoinsFlyEffect");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Native/NativeBridge"),
          u = e("../Framework/Utils/Utils"),
          d = cc._decorator,
          p = d.ccclass,
          f = d.property,
          h = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprCoins = []),
                (t.sprDiamonds = []),
                (t.nodeCoins = null),
                (t.nodeDiamonds = null),
                (t.goldTargetPos = null),
                (t.diaTargetPos = null),
                (t._flySpriteArray = []),
                (t._finishCallback = null),
                (t._gold = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                (this.nodeCoins.active = !1),
                  (this.nodeDiamonds.active = !1),
                  u.default.localStr(this.node),
                  console.log("goldPos: " + this.goldTargetPos.position);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.playFlyEffect = function (e, t, n, o) {
                var a = this;
                void 0 === n && (n = 0), (this._finishCallback = o);
                var i = cc.winSize.height,
                  r = i / 2 - 55;
                if (
                  (l.default.isAndroid() && (r = i / 2 - 125),
                  e == s.FlyEffectType.Coins)
                ) {
                  (this.nodeCoins.active = !0),
                    (this.nodeDiamonds.active = !1),
                    (this._flySpriteArray = this.sprCoins);
                  for (
                    var u = 0, d = 0.2, p = 0;
                    p < this._flySpriteArray.length;
                    p++
                  ) {
                    var f = d + 0.05 * p,
                      h = cc.moveTo(f, cc.v2(this.goldTargetPos.x, r));
                    this._flySpriteArray[p].runAction(
                      cc.sequence(
                        cc.spawn(h, cc.scaleTo(f, 0.8)),
                        cc.delayTime(0.2),
                        cc.hide(),
                        cc.callFunc(function () {
                          (u += 1) == a._flySpriteArray.length &&
                            (a._finishCallback && a._finishCallback(),
                            a.onClose());
                        })
                      )
                    );
                  }
                } else {
                  this.nodeDiamonds,
                    (this.nodeCoins.active = !1),
                    (this.nodeDiamonds.active = !0),
                    (this._flySpriteArray = this.sprDiamonds);
                  var g = 0;
                  for (d = 0.2, p = 0; p < this._flySpriteArray.length; p++)
                    (f = d + 0.05 * p),
                      (h = cc.moveTo(f, cc.v2(this.diaTargetPos.x, r))),
                      this._flySpriteArray[p].runAction(
                        cc.sequence(
                          cc.spawn(h, cc.scaleTo(f, 0.8)),
                          cc.delayTime(0.2),
                          cc.hide(),
                          cc.callFunc(function () {
                            (g += 1) == a._flySpriteArray.length &&
                              (a._finishCallback && a._finishCallback(),
                              a.onClose());
                          })
                        )
                      );
                }
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Get_Coins);
              }),
              (t.prototype.onBtnGetGoldClick = function () {
                this._finishCallback && this._finishCallback(), this.onClose();
              }),
              i([f(cc.Node)], t.prototype, "sprCoins", void 0),
              i([f(cc.Node)], t.prototype, "sprDiamonds", void 0),
              i([f(cc.Node)], t.prototype, "nodeCoins", void 0),
              i([f(cc.Node)], t.prototype, "nodeDiamonds", void 0),
              i([f(cc.Node)], t.prototype, "goldTargetPos", void 0),
              i([f(cc.Node)], t.prototype, "diaTargetPos", void 0),
              i([p], t)
            );
          })(r.default);
        (n.default = h), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    CoinsNotEnoughView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "9c15fLorcNK879cIqHpaL2q", "CoinsNotEnoughView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = cc._decorator,
          l = c.ccclass,
          u =
            (c.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.start = function () {}),
                (t.prototype.onClickRecharge = function () {
                  var e = this;
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "TimingBoxView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node;
                    }
                  );
                }),
                i([l], t)
              );
            })(r.default));
        (n.default = u), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
      },
    ],
    ColorAssembler2d: [
      function (e, t) {
        "use strict";
        cc._RF.push(t, "26a62NvjJ5OYoWrI4n6TYyg", "ColorAssembler2d"),
          cc.Class({
            extends: cc.Component,
            properties: { colors: [cc.Color] },
            onLoad: function () {},
            onEnable: function () {
              cc.director.once(
                cc.Director.EVENT_AFTER_DRAW,
                this._updateColors,
                this
              );
            },
            onDisable: function () {
              cc.director.off(
                cc.Director.EVENT_AFTER_DRAW,
                this._updateColors,
                this
              ),
                (this.node._renderFlag |= cc.RenderFlow.FLAG_COLOR);
            },
            _updateColors: function () {
              var e = this.getComponent(cc.RenderComponent);
              if (e) {
                var t = e._assembler;
                if (t instanceof cc.Assembler2D) {
                  var n = t._renderData.uintVDatas[0];
                  if (n)
                    for (
                      var o = this.node.color,
                        a = t.floatsPerVert,
                        i = 0,
                        r = t.colorOffset,
                        s = n.length;
                      r < s;
                      r += a
                    )
                      n[r] = (this.colors[i++] || o)._val;
                }
              }
            },
          }),
          cc._RF.pop();
      },
      {},
    ],
    CountryItem: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "fff50CPOkxKCZhm+ECFQuv4", "CountryItem");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = cc._decorator,
          u = l.ccclass,
          d = l.property,
          p = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprSelect = null),
                (t.sprCountry = null),
                (t.labCountryName = null),
                (t._countryCode = ""),
                (t._countryName = ""),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents();
              }),
              (t.prototype.start = function () {}),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.User_Info_Select_Country,
                  this.onSelectCountry,
                  this
                );
              }),
              (t.prototype.setInfo = function (e, t, n) {
                var o = this;
                (this._countryCode = e),
                  (this._countryName = t),
                  this.setSelect(n),
                  (this.labCountryName.string = t);
                var a;
                (a =
                  "" == e
                    ? s.PLAYER_COUNTRY_ICON_PATH + "country_icon_default"
                    : s.PLAYER_COUNTRY_ICON_PATH + "country_icon_" + e),
                  this.loadRes(a, cc.SpriteFrame, function (e) {
                    o.sprCountry.spriteFrame = e;
                  });
              }),
              (t.prototype.setSelect = function (e) {
                this.sprSelect.active = e;
              }),
              (t.prototype.onClickSelect = function () {
                this.setSelect(!0),
                  cc.director.emit(
                    c.GameEvent.User_Info_Select_Country,
                    this._countryCode,
                    this._countryName
                  );
              }),
              (t.prototype.getCountryCode = function () {
                return this._countryCode;
              }),
              (t.prototype.onSelectCountry = function (e) {
                this._countryCode != e && this.setSelect(!1);
              }),
              i([d(cc.Node)], t.prototype, "sprSelect", void 0),
              i([d(cc.Sprite)], t.prototype, "sprCountry", void 0),
              i([d(cc.Label)], t.prototype, "labCountryName", void 0),
              i([u], t)
            );
          })(r.default);
        (n.default = p), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
      },
    ],
    DiceTestUI: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "e9f49R6kZxBDrMYZkufU5YY", "DiceTestUI");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Enum/GameEnum"),
          s = e("../../Framework/Utils/Utils"),
          c = cc._decorator,
          l = c.ccclass,
          u =
            (c.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.start = function () {}),
                (t.prototype.onClickClose = function () {
                  this.node.destroy();
                }),
                (t.prototype.onClickRollDice = function (e, t) {
                  if ("random" == t) {
                    var n = s.default.getRandomNum(1, 6);
                    cc.director.emit(r.GameEvent.Roll_The_Dice_Test, n);
                  } else
                    (n = parseInt(t)),
                      cc.director.emit(r.GameEvent.Roll_The_Dice_Test, n);
                  this.node.active = !1;
                }),
                i([l], t)
              );
            })(cc.Component));
        (n.default = u), cc._RF.pop();
      },
      {
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    Dice: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "cf0f0/No4dNyI7J0fJ6QNsa", "Dice");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Manager/ShopDataManager"),
          l = cc._decorator,
          u = l.ccclass,
          d = l.property,
          p = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.animDice = null),
                (t.sprDice = null),
                (t._dicePoints = 1),
                (t._finishCallback = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.start = function () {}),
              (t.prototype.playDiceAnim = function (e, t) {
                this.animDice.play("dice_anim"),
                  (this._dicePoints = e),
                  (this._finishCallback = t),
                  this.animDice.on("finished", this.onFinished, this);
              }),
              (t.prototype.onFinished = function () {
                this.animDice.off("finished", this.onFinished, this);
                var e = c.default.getInstance().getSelectDice(),
                  t =
                    s.SKIN_PICTURE_PATH +
                    e +
                    "_dice_points_" +
                    this._dicePoints;
                this.setDiceRes(this.sprDice, t),
                  this._finishCallback && this._finishCallback();
              }),
              (t.prototype.setDiceRes = function (e, t) {
                this.loadRes(t, cc.SpriteFrame, function (t) {
                  e.spriteFrame = t;
                });
              }),
              (t.prototype.stopDiceAnim = function () {
                this.animDice.stop();
              }),
              (t.prototype.diceAnimEnd = function () {}),
              i([d(cc.Animation)], t.prototype, "animDice", void 0),
              i([d(cc.Sprite)], t.prototype, "sprDice", void 0),
              i([u], t)
            );
          })(r.default);
        (n.default = p), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Manager/ShopDataManager": "ShopDataManager",
      },
    ],
    EntryScene: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "acaa2PAoQNIb6b8uFYg3QX0", "EntryScene");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AtlasResManager"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Manager/UserInfoManager"),
          p = e("../Framework/Native/NativeBridge"),
          f = e("../Framework/Utils/Utils"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (t.label_bar = null), (t.img_bar = null), t;
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                p.default.init();
                var e = f.default.getCurTimeStamp();
                c.default.getInstance().loadRoomPrefab(
                  function () {
                    c.default.getInstance().loadAtlasRes(function (t) {
                      l.default.getInstance().isBuried &&
                        l.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: "ludo_game_download_resource",
                            resId: t[0]._uuid,
                            result: !0,
                            time: f.default.getCurTimeStamp() - e,
                          }),
                        d.default.getInstance().hasLocalUserInfo()
                          ? (cc.director.loadScene("Hall"),
                            u.default.getInstance().setIsNewPlay(!1))
                          : (d.default.getInstance().genMyselfUserId(),
                            cc.director.loadScene("Hall"),
                            u.default.getInstance().setIsNewPlay(!0)),
                        l.default.getInstance().isBuried &&
                          l.default
                            .getInstance()
                            .sendBuriedPointInfo({
                              event: "ludo_game_render",
                              time: f.default.getCurTimeStamp() - e,
                              resId: "0",
                              result: !0,
                            });
                    });
                  },
                  this.label_bar,
                  this.img_bar
                ),
                  console.log("start-------onLoad-----------");
                var t = p.default.getData(s.DataSaveKey.Language_Type);
                d.default.getInstance().getActivityCountry(),
                  console.log("start-------onLoad-----------: " + t),
                  console.log(
                    "\u5f00\u59cb\u52a0\u8f7d\uff1a " +
                      f.default.getCurTimeStamp()
                  ),
                  "" == t &&
                    (console.log(
                      "start-------onLoad-----------_languageType: " + t
                    ),
                    d.default.getInstance().getAppLanguage()),
                  u.default.getInstance().setSceneType(s.SceneType.Entry),
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({ event: s.BuriedOneKey.appOpen }),
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedOneKey.enterGameHall,
                      actionName: s.BuriedTwoKey.fromAppOpen,
                    });
              }),
              (t.prototype.start = function () {}),
              i([m(cc.Label)], t.prototype, "label_bar", void 0),
              i([m(cc.Sprite)], t.prototype, "img_bar", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AtlasResManager": "AtlasResManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    GameConst: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "c5081qfXp5CtoQYhlu60RM2", "GameConst"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.GREY2 =
            n.BROWN =
            n.GREEN =
            n.GREY =
            n.YELLOW =
            n.BLUE =
            n.ISAPPLET =
            n.BROWSER_ATHENA =
            n.GET_GOLD =
            n.SNAKERS_MAP_MAX_COUNT =
            n.TASK_REWARD_RANDOM =
            n.TASK_LAN_NUM =
            n.TASK_JIN_NUM =
            n.AD_REWARD_CD_TIME =
            n.AD_LOADING_CD_TIME =
            n.DESIGN_RESOLUTION_HEIGHT =
            n.DESIGN_RESOLUTION_WIDTH =
            n.LANGUAGE_IMG_PATH =
            n.LOCAL =
            n.SNAKERS_AND_LADDERS =
            n.CMN =
            n.ONLINE_REWARD =
            n.TASK_IMG_PATH =
            n.COMMON_PREFAB_PATH =
            n.ANIMATION_PREFAB_PATH =
            n.GAME_PREFAB_PATH =
            n.HALL_PREFAB_PATH =
            n.LOGIN_PREFAB_PATH =
            n.SKIN_PICTURE_PATH =
            n.PLAYER_COUNTRY_ICON_PATH =
            n.PLAYER_HEAD_PHOTO_PATH =
            n.TURNTABLE_ADBONUS =
            n.TURNTABLE_LEFT_SPIN_COUNT =
            n.TURNTABLE_CD_TIME =
            n.TIMINGBOX_AD_COUNT_LIMIT =
            n.TIMINGBOX_REFRESH_TIME =
            n.PLAYER_MAX_OUT_TIME_COUNT =
            n.ARRAY_ELE_NOT_EXIST =
            n.PLAYER_HEAD_PHOTO_COUNT =
            n.PLAYER_AGAIN_ROLL_CD_TIME =
            n.PLATER_AGAIN_ROLL_COUNT =
            n.PLAYER_OPT_CD_TIME =
            n.CHESS_COLOR_COUNT =
            n.PLAYER_CHESS_COUNT =
            n.DICE_MAX_POINTS =
              void 0),
          (n.DICE_MAX_POINTS = 6),
          (n.PLAYER_CHESS_COUNT = 4),
          (n.CHESS_COLOR_COUNT = 4),
          (n.PLAYER_OPT_CD_TIME = 15),
          (n.PLATER_AGAIN_ROLL_COUNT = 3),
          (n.PLAYER_AGAIN_ROLL_CD_TIME = 2.5),
          (n.PLAYER_HEAD_PHOTO_COUNT = 16),
          (n.ARRAY_ELE_NOT_EXIST = -1),
          (n.PLAYER_MAX_OUT_TIME_COUNT = 5),
          (n.TIMINGBOX_REFRESH_TIME = 3600),
          (n.TIMINGBOX_AD_COUNT_LIMIT = 5),
          (n.TURNTABLE_CD_TIME = 3600),
          (n.TURNTABLE_LEFT_SPIN_COUNT = 4),
          (n.TURNTABLE_ADBONUS = 3),
          (n.PLAYER_HEAD_PHOTO_PATH = "Texture/head_photo/"),
          (n.PLAYER_COUNTRY_ICON_PATH = "Texture/country/"),
          (n.SKIN_PICTURE_PATH = "Texture/skin/"),
          (n.LOGIN_PREFAB_PATH = "Prefab/Login/prefab/"),
          (n.HALL_PREFAB_PATH = "Prefab/Hall/prefab/"),
          (n.GAME_PREFAB_PATH = "Prefab/Game/prefab/"),
          (n.ANIMATION_PREFAB_PATH = "Prefab/Animation/"),
          (n.COMMON_PREFAB_PATH = "Prefab/Common/"),
          (n.TASK_IMG_PATH = "Texture/task/"),
          (n.ONLINE_REWARD = "Texture/online/"),
          (n.CMN = "Texture/cmn/"),
          (n.SNAKERS_AND_LADDERS = "Texture/snakers_and_ladders/"),
          (n.LOCAL = "Texture/localMode/"),
          (n.LANGUAGE_IMG_PATH = "Texture/language/"),
          (n.DESIGN_RESOLUTION_WIDTH = 720),
          (n.DESIGN_RESOLUTION_HEIGHT = 1080),
          (n.AD_LOADING_CD_TIME = 8),
          (n.AD_REWARD_CD_TIME = 1800),
          (n.TASK_JIN_NUM = 1),
          (n.TASK_LAN_NUM = 4),
          (n.TASK_REWARD_RANDOM = 2),
          (n.SNAKERS_MAP_MAX_COUNT = 5),
          (n.GET_GOLD = 3e3),
          (n.BROWSER_ATHENA = !0),
          (n.ISAPPLET = !1),
          (n.BLUE = cc.color(0, 89, 139)),
          (n.YELLOW = cc.color(154, 85, 2)),
          (n.GREY = cc.color(120, 120, 120)),
          (n.GREEN = cc.color(0, 127, 0)),
          (n.BROWN = cc.color(152, 90, 7)),
          (n.GREY2 = cc.color(71, 70, 70)),
          cc._RF.pop();
      },
      {},
    ],
    GameDataManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "4c20d91MfBIyoEgNqkWlFfp", "GameDataManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../../Common/Tools"),
          a = e("../Enum/GameEnum"),
          i = e("../Native/NativeBridge"),
          r = e("../Utils/Utils"),
          s = (function () {
            function e() {
              (this._dicePoints = 0),
                (this._isFirstEnterGame = !0),
                (this._payInitSuccess = null),
                (this._hallGoldPos = null),
                (this._hallDiamondPos = null),
                (this._isWatchADOut = !1),
                (this._winGoldQuit = 0),
                (this._curSceneType = a.SceneType.Entry),
                (this._propTipsCount = {}),
                (this._isUpgrade = !1),
                (this._isPopupNoNetwork = !1),
                (this._isAd = !1),
                (this._roundCount = 0),
                (this._gameType = a.GameType.Ludo),
                (this._snakersMapIndex = 1),
                (this._exitType = 0),
                (this._isAgain = !1),
                (this._openRoom = !1),
                (this._newPlay = !0),
                (this._openAppPlayGameCount = 0),
                (this._firstSixIndex = 0),
                (this._myBeEatenOther = 0),
                (this._eatOther = 0),
                (this._firstEatChessTime = 0),
                (this._undoCount = 0),
                (this._isSafe = !0),
                (this._undoIndex = 0),
                (this.gameUndoCount = 5),
                (this._openApp = !0),
                (this._isCompleteUndoPower = !1),
                (this._isOpenUser = !1),
                (this._isCompleteGuide = !1),
                (this._isGetAppletReward = !1),
                (this.showAppTip = !0),
                (this.canUseBomb = !0),
                (this.isUndoDice = !1),
                (this.isWin = !1),
                (this._localInfo = {}),
                (this.bomb = {}),
                (this._propTipsCount[a.PropType.Bomb] = 0),
                (this._propTipsCount[a.PropType.Protective] = 0);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.getTools = function () {
                return cc.find("toolsNode").getComponent(o.default);
              }),
              (e.prototype.setPayInitSuccess = function (e) {
                this._payInitSuccess = e;
              }),
              (e.prototype.isPayInitSuccess = function () {
                return this._payInitSuccess;
              }),
              (e.prototype.setDicePoints = function (e) {
                this._dicePoints = e;
              }),
              (e.prototype.getDicePoints = function () {
                return this._dicePoints;
              }),
              (e.prototype.setGameType = function (e) {
                this._gameType = e;
              }),
              (e.prototype.getGameType = function () {
                return this._gameType;
              }),
              (e.prototype.getTriangleRotation = function (e, t) {
                if (e == a.PlayerIndex.LeftBottom) {
                  if (t == a.ChessColor.Blue) return 0;
                  if (t == a.ChessColor.Red) return -90;
                  if (t == a.ChessColor.Green) return 180;
                  if (t == a.ChessColor.Yellow) return 90;
                } else if (e == a.PlayerIndex.LeftTop) {
                  if (t == a.ChessColor.Blue) return 90;
                  if (t == a.ChessColor.Red) return 0;
                  if (t == a.ChessColor.Green) return -90;
                  if (t == a.ChessColor.Yellow) return 180;
                } else if (e == a.PlayerIndex.RightTop) {
                  if (t == a.ChessColor.Blue) return 180;
                  if (t == a.ChessColor.Red) return 90;
                  if (t == a.ChessColor.Green) return 0;
                  if (t == a.ChessColor.Yellow) return -90;
                } else if (e == a.PlayerIndex.RightBottom) {
                  if (t == a.ChessColor.Blue) return -90;
                  if (t == a.ChessColor.Red) return 180;
                  if (t == a.ChessColor.Green) return 90;
                  if (t == a.ChessColor.Yellow) return 0;
                }
              }),
              (e.prototype.setFristEnterGame = function (e) {
                (this._isFirstEnterGame = e),
                  i.default.saveData(
                    a.DataSaveKey.IsFirstEnterGame,
                    JSON.stringify(e)
                  );
              }),
              (e.prototype.isFirstEnterGame = function () {
                return "" != i.default.getData(a.DataSaveKey.IsFirstEnterGame)
                  ? JSON.parse(
                      i.default.getData(a.DataSaveKey.IsFirstEnterGame)
                    )
                  : this._isFirstEnterGame;
              }),
              (e.prototype.setHallGoldPos = function (e) {
                this._hallGoldPos = e;
              }),
              (e.prototype.getHallGoldPos = function () {
                return this._hallGoldPos;
              }),
              (e.prototype.setHallDiamondPos = function (e) {
                this._hallDiamondPos = e;
              }),
              (e.prototype.getHallDiamondPos = function () {
                return this._hallDiamondPos;
              }),
              (e.prototype.setWatchADOut = function (e) {
                this._isWatchADOut = e;
              }),
              (e.prototype.isWatchADOut = function () {
                return this._isWatchADOut;
              }),
              (e.prototype.setWinGoldQuit = function (e) {
                this._winGoldQuit = e;
              }),
              (e.prototype.getWinGoldQuit = function () {
                return this._winGoldQuit;
              }),
              (e.prototype.setSceneType = function (e) {
                this._curSceneType = e;
              }),
              (e.prototype.getCurrentSceneType = function () {
                return this._curSceneType;
              }),
              (e.prototype.addPropTipsCount = function (e) {
                this._propTipsCount[e] = this._propTipsCount[e] + 1;
              }),
              (e.prototype.isShowPropTips = function (e) {
                return this._propTipsCount[e] < 1;
              }),
              (e.prototype.setUpgrade = function (e) {
                this._isUpgrade = e;
              }),
              (e.prototype.isUpgrade = function () {
                return this._isUpgrade;
              }),
              (e.prototype.setPopupNoNetwork = function (e) {
                this._isPopupNoNetwork = e;
              }),
              (e.prototype.isPopupNoNetwork = function () {
                return this._isPopupNoNetwork;
              }),
              (e.prototype.setIsAd = function (e) {
                this._isAd = e;
              }),
              (e.prototype.getIsAd = function () {
                return this._isAd;
              }),
              (e.prototype.setRoundCount = function (e) {
                this._roundCount = e;
              }),
              (e.prototype.getRoundCount = function () {
                return this._roundCount;
              }),
              (e.prototype.setSnakersMapIndex = function (e) {
                this._snakersMapIndex = e;
              }),
              (e.prototype.getSnakersMapIndex = function () {
                return this._snakersMapIndex;
              }),
              (e.prototype.setExitType = function (e) {
                this._exitType = e;
              }),
              (e.prototype.getExitType = function () {
                return this._exitType;
              }),
              (e.prototype.setIsAgain = function (e) {
                this._isAgain = e;
              }),
              (e.prototype.getIsAgain = function () {
                return this._isAgain;
              }),
              (e.prototype.setOpenRoom = function (e) {
                this._openRoom = e;
              }),
              (e.prototype.getOpenRoom = function () {
                return this._openRoom;
              }),
              (e.prototype.getIsNewPlay = function () {
                return this._newPlay;
              }),
              (e.prototype.setIsNewPlay = function (e) {
                (this._newPlay = e),
                  i.default.saveData(
                    a.DataSaveKey.Is_New_Play,
                    JSON.stringify(this._newPlay)
                  );
              }),
              (e.prototype.getLocalInfo = function () {
                return this._localInfo;
              }),
              (e.prototype.setLocalInfo = function (e, t, n) {
                this._localInfo[e] || (this._localInfo[e] = {});
                var o = { isComputer: !1, isNull: !1 };
                (o.isComputer = t),
                  n && ((o.isComputer = !1), (o.isNull = n)),
                  (this._localInfo[e] = o);
              }),
              (e.prototype.deleLocalInfo = function (e) {
                this._localInfo[e] && delete this._localInfo[e];
              }),
              (e.prototype.getOpenAppPlayGameCount = function () {
                return this._openAppPlayGameCount;
              }),
              (e.prototype.setOpenAppPlayGameCount = function () {
                this._openAppPlayGameCount++;
              }),
              (e.prototype.getFirstSixIndex = function () {
                return this._firstSixIndex;
              }),
              (e.prototype.setFirstSixIndex = function (e) {
                this._firstSixIndex = e;
              }),
              (e.prototype.getMyBeEatenOther = function () {
                return this._myBeEatenOther;
              }),
              (e.prototype.setMyBeEatenOther = function () {
                this._myBeEatenOther++;
              }),
              (e.prototype.getEatOther = function () {
                return this._eatOther;
              }),
              (e.prototype.setEatOther = function () {
                this._eatOther++,
                  1 == this._eatOther &&
                    (this._firstEatChessTime = r.default.getCurTimeStamp());
              }),
              (e.prototype.getFirstEatChessTime = function () {
                return this._firstEatChessTime;
              }),
              (e.prototype.getUndoCount = function () {
                return this._undoCount;
              }),
              (e.prototype.setUndoCount = function () {
                this._undoCount++;
              }),
              (e.prototype.getIsSafe = function () {
                return this._isSafe;
              }),
              (e.prototype.setIsSafe = function (e) {
                this._isSafe = e;
              }),
              (e.prototype.getUndoIndex = function () {
                return this._undoIndex;
              }),
              (e.prototype.setUndoIndex = function (e) {
                this._undoIndex = e;
              }),
              (e.prototype.getGameUndoCount = function () {
                return this.gameUndoCount;
              }),
              (e.prototype.setGameUndoCount = function (e) {
                this.gameUndoCount = e;
              }),
              (e.prototype.setOpenApp = function (e) {
                this._openApp = e;
              }),
              (e.prototype.getOpenApp = function () {
                return this._openApp;
              }),
              (e.prototype.getIsCompleteUndoPower = function () {
                var e = i.default.getData(a.DataSaveKey.IsCompletedUndoPower);
                return (
                  e && (this._isCompleteUndoPower = JSON.parse(e)),
                  this._isCompleteUndoPower
                );
              }),
              (e.prototype.setIsCompleteUndoPower = function (e) {
                (this._isCompleteUndoPower = e),
                  i.default.saveData(
                    a.DataSaveKey.IsCompletedGuide,
                    JSON.stringify(this._isCompleteUndoPower)
                  );
              }),
              (e.prototype.setIsOpenUser = function (e) {
                this._isOpenUser = e;
              }),
              (e.prototype.getIsOpenUser = function () {
                return this._isOpenUser;
              }),
              (e.prototype.setIsCompleteGuide = function (e) {
                (this._isCompleteGuide = e),
                  i.default.saveData(
                    a.DataSaveKey.Applet_Guide,
                    JSON.stringify(this._isCompleteGuide)
                  );
              }),
              (e.prototype.getIsCompleteGuide = function () {
                var e = i.default.getData(a.DataSaveKey.Applet_Guide);
                return (
                  e && (this._isCompleteGuide = JSON.parse(e)),
                  this._isCompleteGuide
                );
              }),
              (e.prototype.setIsGetAppletReward = function (e) {
                (this._isGetAppletReward = e),
                  i.default.saveData(
                    a.DataSaveKey.Applet_Get_Reward,
                    JSON.stringify(this._isGetAppletReward)
                  );
              }),
              (e.prototype.getIsGetAppletReward = function () {
                var e = i.default.getData(a.DataSaveKey.Applet_Get_Reward);
                return (
                  e && (this._isGetAppletReward = JSON.parse(e)),
                  this._isGetAppletReward
                );
              }),
              (e.prototype.setBombInfo = function (e) {
                this.bomb[e] ? (this.bomb[e] += 1) : (this.bomb[e] = 1);
              }),
              (e.prototype.getBomb = function (e) {
                var t = 0;
                return this.bomb[e] && (t = this.bomb[e]), t;
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = s), cc._RF.pop();
      },
      {
        "../../Common/Tools": "Tools",
        "../Enum/GameEnum": "GameEnum",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
      },
    ],
    GameEnum: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "45a82gAfdhLaZRcIMq8/eP2", "GameEnum"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.Item =
            n.SkinGetType =
            n.activityState =
            n.circulateActivity =
            n.Entrance =
            n.LanguageType =
            n.SkinType =
            n.GoldType =
            n.TaskType =
            n.TaskQuality =
            n.TaskStatus =
            n.BuyStatus =
            n.PopupButtonClickType =
            n.LuckChangeType =
            n.CloudControlConfigKey =
            n.BuriedTwoKey =
            n.BuriedOneKey =
            n.BuriedPointSecondKey =
            n.BuriedPointKey =
            n.ButtonClickType =
            n.MidwayQuitType =
            n.ADRewardType =
            n.TimingBoxRewardType =
            n.RegisterType =
            n.ADType =
            n.AudioType =
            n.NetworkStatus =
            n.GameResult =
            n.GameDifficulty =
            n.SceneType =
            n.FlyEffectType =
            n.ShopShowType =
            n.PropType =
            n.MapType =
            n.RewardStatus =
            n.DataSaveKey =
            n.PlayerIndex =
            n.PlayerCount =
            n.ChessColor =
            n.GameType =
            n.GameRoomMode =
            n.GameMode =
            n.GameEvent =
              void 0),
          (function (e) {
            (e.Login = "Event_Login"),
              (e.Update_Nick_Name = "Event_Update_Nick_Name"),
              (e.Update_Country_Code = "Event_Update_Country_Code"),
              (e.Update_Gold_Num = "Event_Update_Gold_Num"),
              (e.Update_Diamond_Num = "Event_Update_Diamond_Num"),
              (e.Update_Skin_Num = "Event_Update_Skin_Num"),
              (e.Update_Cur_Level = "Event_Update_Cur_Level"),
              (e.Update_Cur_Exp = "Event_Update_Cur_Exp"),
              (e.Update_HeadPhoto = "Event_Update_HeadPhoto"),
              (e.Watch_Video_Finish = "Event_Watch_Video_Finish"),
              (e.Recharge_Success = "Event_Recharge_Success"),
              (e.Recharge_Failed = "Event_Recharge_Failed"),
              (e.Remove_Barrier = "Event_Remove_Barrier"),
              (e.Turn_Player_Operation = "Event_Turn_Player_Operation"),
              (e.Player_Operation_Completed =
                "Event_Player_Operation_Completed"),
              (e.Player_Operation_OutTime = "Event_Player_Operation_OutTime"),
              (e.Roll_The_Dice = "Event_Roll_The_Dice"),
              (e.Roll_The_Dice_AI = "Event_Roll_The_Dice_AI"),
              (e.Roll_The_Dice_Test = "Event_Roll_The_Dice_Test"),
              (e.Hide_Dice_TestUI = "Event_Hide_Dice_TestUI"),
              (e.Popup_Match_Player = "Event_Popup_Match_Player"),
              (e.Game_Over = "Event_Game_Over"),
              (e.Player_Walk_Start = "Event_Player_Walk_Start"),
              (e.Bakc_To_Hall = "Event_Back_To_Hall"),
              (e.FirstRank_Back_To_Hall = "Event_FirstRank_Back_To_Hall"),
              (e.TimingBox_Coins_AD_Refresh =
                "Event_TimingBox_Coins_AD_Refresh"),
              (e.TimingBox_Diamonds_AD_Refresh =
                "Event_TimingBox_Diamonds_AD_Refresh"),
              (e.TimingBox_Get_Coins = "Event_TimingBox_Get_Coins"),
              (e.User_Info_Modify_Success = "Event_User_Info_Modify_Success"),
              (e.User_Info_Select_HeadPhoto =
                "Event_User_Info_Select_HeadPhoto"),
              (e.User_Info_Select_Country = "Event_User_Info_Select_Country"),
              (e.Select_Skin = "Event_Select_Skin"),
              (e.Turntable_CD_Refresh = "Event_Turntable_CD_Refresh"),
              (e.Turntable_Show_Get_Reward = "Event_Turntable_Show_Get_Reward"),
              (e.Turntable_Spin_Again = "Event_Turntable_Spin_Again"),
              (e.Guess_Size_Roll_Dice_Finish =
                "Event_Guess_Size_Roll_Dice_Finish"),
              (e.Chess_Arrive_Terminal = "Event_Chess_Arrive_Terminal"),
              (e.Show_Guess_Size_UI = "Event_Show_Guess_Size_UI"),
              (e.Update_Shop_Skin_UI = "Event_Update_Shop_Skin_UI"),
              (e.Unlock_Skin = "Event_Unlock_Skin"),
              (e.AD_Cache_Success = "Event_AD_Cache_Success"),
              (e.AD_Cache_Fail = "Event_AD_Cache_Fail"),
              (e.Check_Level_Upgrade = "Event_Check_Level_Upgrade"),
              (e.Move_Map_Node = "Event_Move_Map_Node"),
              (e.Show_Win_Player_Flag = "Event_Show_Win_Player_Flag"),
              (e.Show_Quit_Prize_View = "Event_Show_Quit_Prize_View"),
              (e.Refresh_Player_Luck_Info = "Event_Refresh_Player_Luck_Info"),
              (e.Show_Popular_View = "Event_Show_Popular_View"),
              (e.Show_Sign_View = "Event_Show_Sign_View"),
              (e.Update_Task = "Event_Update_Task"),
              (e.Use_Shop_Skin = "Event_Use_Shop_Skin"),
              (e.Update_Online_Reward = "Event_Update_Online_Reward"),
              (e.Update_Shop_Skin_Info = "Event_Update_Shop_Skin_Info"),
              (e.Select_Shop_Skin = "Event_Select_Shop_Skin"),
              (e.Update_Ad_Skin = "Event_Update_Ad_Skin"),
              (e.Update_Select_Token = "Event_Update_Select_Token"),
              (e.Update_Select_Board = "Event_Update_Select_Board"),
              (e.Update_Select_Dice = "Event_Update_Select_Dice"),
              (e.Shop_Select_Skin = "Event_Shop_Select_Skin"),
              (e.Update_Shop_Cell_Grid = "Event_Update_Shop_Cell_Grid"),
              (e.Player_Snakers_Completed = "Event_Player_Snakers_Completed"),
              (e.Play_Snakers_Anim = "Event_Play_Snakers_Anim"),
              (e.Show_Exit_Game = "Event_Show_Exit_Game"),
              (e.Game_Load = "Event_Game_Load"),
              (e.Play_Close_Audio = "Event_Play_Close_Audio"),
              (e.Add_Player = "Event_Add_Player"),
              (e.Del_Player = "Event_Del_Player"),
              (e.Select_Language = "Evena_Select_Language"),
              (e.send_Expression = "Event_Send_Expression"),
              (e.send_Sentence = "Event_Send_Sentence"),
              (e.delect_Expression = "Event_Delect_Expression"),
              (e.twoRobat_Expression = "Event_Two_Robat_Expression"),
              (e.eatChess = "Event_Eat_Chess"),
              (e.Guide_Select_Chess = "Event_Guide_Select_Chess"),
              (e.Show_Guide = "Event_Show_Guide"),
              (e.Show_Guide_Safe = "Event_Show_Guide_Safe"),
              (e.Close_Guide_Ui = "Event_Close_Guide_Ui"),
              (e.Select_Undo_Index = "Event_Select_Undo_Index"),
              (e.Show_Undo_Node = "Event_Show_Undo_Node"),
              (e.Use_Undo = "Event_Use_Undo"),
              (e.Show_Undo_Help = "Event_Show_Undo_Help"),
              (e.Get_Online_Reward = "Event_Get_Online_Reward"),
              (e.Get_Box_Reward = "Event_Get_Box_Reward"),
              (e.Close_ShopInfo = "Event_Close_ShopInfo"),
              (e.Show_Undo_Dice = "Event_Show_Undo_Dice"),
              (e.Close_Undo_Dice = "Event_Close_Undo_Dice"),
              (e.Show_SignReward = "Event_Show_SignReward"),
              (e.Open_Activity = "Event_Open_Activity"),
              (e.Open_ActivityMain = "Event_Open_ActivityMain"),
              (e.Close_Parent_Ui = "Event_Close_Parent_Ui"),
              (e.Show_Hall_Icon = "Event_Show_Hall_Icon"),
              (e.Update_Applet_Icon = "Event_Update_Applet_Icon"),
              (e.showActivityMatch = "Event_showActivityMatch"),
              (e.showActivityHelp = "Event_showActivityHelp"),
              (e.showActivityCup = "Event_showActivityCup"),
              (e.closeActivity = "Event_closeActivity"),
              (e.ShowBombHelpTip = "Event_ShowBombHelpTip"),
              (e.ShowBomb = "Event_ShowBomb"),
              (e.UpdateBombCount = "Event_UpdateBombCount"),
              (e.undoDice = "Event_undoDice");
          })(n.GameEvent || (n.GameEvent = {})),
          (function (e) {
            (e[(e.Online = 0)] = "Online"),
              (e[(e.Computer = 1)] = "Computer"),
              (e[(e.Local = 2)] = "Local"),
              (e[(e.BombItem = 3)] = "BombItem"),
              (e[(e.Roadblock = 4)] = "Roadblock");
          })(n.GameMode || (n.GameMode = {})),
          (function (e) {
            (e[(e.Quick = 0)] = "Quick"),
              (e[(e.Classic = 1)] = "Classic"),
              (e[(e.Local = 2)] = "Local");
          })(n.GameRoomMode || (n.GameRoomMode = {})),
          (function (e) {
            (e[(e.Ludo = 0)] = "Ludo"),
              (e[(e.SnakerAndLadders = 1)] = "SnakerAndLadders");
          })(n.GameType || (n.GameType = {})),
          (function (e) {
            (e[(e.Blue = 0)] = "Blue"),
              (e[(e.Red = 1)] = "Red"),
              (e[(e.Green = 2)] = "Green"),
              (e[(e.Yellow = 3)] = "Yellow");
          })(n.ChessColor || (n.ChessColor = {})),
          (function (e) {
            (e[(e.Two = 2)] = "Two"),
              (e[(e.Four = 4)] = "Four"),
              (e[(e.Six = 6)] = "Six"),
              (e[(e.Eight = 8)] = "Eight");
          })(n.PlayerCount || (n.PlayerCount = {})),
          (function (e) {
            (e[(e.LeftBottom = 0)] = "LeftBottom"),
              (e[(e.LeftTop = 1)] = "LeftTop"),
              (e[(e.RightTop = 2)] = "RightTop"),
              (e[(e.RightBottom = 3)] = "RightBottom");
          })(n.PlayerIndex || (n.PlayerIndex = {})),
          (function (e) {
            (e.User_Info = "Key_User_Info"),
              (e.ShopGoods_Info = "Key_ShopGoods_Info"),
              (e.Sign_Info = "Key_Sign_Info"),
              (e.TimingBox_Info = "Key_TimingBox_Info"),
              (e.GameSetting_Info = "Key_GameSetting_Info"),
              (e.Prop_Info = "Key_Prop_Info"),
              (e.CustomData_Info = "Key_CustomData_Info"),
              (e.Shop_Info = "Key_Shop_Info"),
              (e.Turntable_Info = "Key_Turntable_Info"),
              (e.GameDifficulty_Info = "Key_GameDifficulty_Info"),
              (e.Luck_Info = "Key_Luck_Info"),
              (e.Skin_Info = "Key_Skin_Info"),
              (e.Task_Info = "Key_Task_Info"),
              (e.Offline_Time_Info = "Key_Offline_Info"),
              (e.Online_Time_Info = "Key_Online_Time_Info"),
              (e.Skin_Item = "Key_Skin_Item"),
              (e.Online_Reward_Info = "Key_Online_Reward_Info"),
              (e.Shop_Skin_Info = "Key_Shop_Skin_Info"),
              (e.Select_Token = "Key_Select_Token"),
              (e.Select_Dice = "Key_Select_Dice"),
              (e.Select_Board = "Key_Select_Board"),
              (e.IsFirstEnterGame = "Key_IsFirstEnterGame"),
              (e.IsEnterGame = "Key_IsEnterGame"),
              (e.Enter_Quick_Mode = "Key_Enter_Quick_Mode"),
              (e.Enter_Classice_Mode = "Key_Enter_Classice_Mode"),
              (e.IsCompletedGuide = "Key_IsCompletedGuide"),
              (e.GetGoldCount = "Key_GetGoldCount"),
              (e.Is_New_Play = "Key_Is_New_Play"),
              (e.Language_Type = "Evena_Select_Language"),
              (e.Login_Info = "Key_Login_Info"),
              (e.ContinuityLostCount = "Key_ContinuityLostCount"),
              (e.GameCount = "Key_GameCount"),
              (e.GameVersion = "Key_GameVersion"),
              (e.IsCompletedUndoPower = "Key_IsCompletedUndoPower"),
              (e.ActivityRewardCount = "Key_ActivityRewardCount"),
              (e.Activityprogress = "Key_Activityprogress"),
              (e.OpenActivityTime = "Key_OpenActivityTime"),
              (e.Time_Reward_End_Time = "Key_TimeRewardEndTime"),
              (e.Applet_Guide = "Key_AppletGuide"),
              (e.Applet_Get_Reward = "Key_Applet_Get_Reward"),
              (e.activityWinCount = "Key_activityWinCount"),
              (e.newTurntableInfo = "Key_newTurntableInfo");
          })(n.DataSaveKey || (n.DataSaveKey = {})),
          (function (e) {
            (e[(e.Got = 0)] = "Got"),
              (e[(e.Can = 1)] = "Can"),
              (e[(e.NotCan = 2)] = "NotCan");
          })(n.RewardStatus || (n.RewardStatus = {})),
          (function (e) {
            (e[(e.Four = 0)] = "Four"),
              (e[(e.Five = 1)] = "Five"),
              (e[(e.Six = 2)] = "Six");
          })(n.MapType || (n.MapType = {})),
          (function (e) {
            (e[(e.AgainRoll = 0)] = "AgainRoll"),
              (e[(e.DoubleDice = 1)] = "DoubleDice"),
              (e[(e.Bomb = 2)] = "Bomb"),
              (e[(e.Protective = 3)] = "Protective");
          })(n.PropType || (n.PropType = {})),
          (function (e) {
            (e[(e.Gold = 0)] = "Gold"),
              (e[(e.Dimaond = 1)] = "Dimaond"),
              (e[(e.Skin = 2)] = "Skin");
          })(n.ShopShowType || (n.ShopShowType = {})),
          (function (e) {
            (e[(e.Coins = 0)] = "Coins"), (e[(e.Diamonds = 1)] = "Diamonds");
          })(n.FlyEffectType || (n.FlyEffectType = {})),
          (function (e) {
            (e[(e.Entry = 0)] = "Entry"),
              (e[(e.Login = 1)] = "Login"),
              (e[(e.Hall = 2)] = "Hall"),
              (e[(e.Game = 3)] = "Game"),
              (e[(e.snakerAndLadders = 4)] = "snakerAndLadders"),
              (e[(e.Guide = 5)] = "Guide");
          })(n.SceneType || (n.SceneType = {})),
          (function (e) {
            (e[(e.Esay = 0)] = "Esay"),
              (e[(e.Normal = 1)] = "Normal"),
              (e[(e.Hard = 2)] = "Hard");
          })(n.GameDifficulty || (n.GameDifficulty = {})),
          (function (e) {
            (e[(e.Fail = 0)] = "Fail"), (e[(e.Success = 1)] = "Success");
          })(n.GameResult || (n.GameResult = {})),
          (function (e) {
            (e[(e.No = -1)] = "No"), (e[(e.Normal = 0)] = "Normal");
          })(n.NetworkStatus || (n.NetworkStatus = {})),
          (function (e) {
            (e.Button_Click = "Audio/button-click"),
              (e.Chess_Walk = "Audio/chess_walk"),
              (e.Roll_Dice = "Audio/roll_dice"),
              (e.Get_Coins = "Audio/get_coins"),
              (e.Player_Opt_CD = "Audio/player_opt_cd"),
              (e.Bomb = "Audio/bomb"),
              (e.Match_Player_Turn = "Audio/match_player_turn"),
              (e.Chess_Arrive_Safe = "Audio/chess_arrive_safe"),
              (e.Chess_Arrive_Terminal = "Audio/chess_arrive_terminal"),
              (e.Chess_Be_Eaten = "Audio/chess_be_eaten"),
              (e.Player_Upgrade = "Audio/player_upgrade"),
              (e.Protective_Disappear = "Audio/protective_dissapear"),
              (e.Rocket_Speed_Up = "Audio/rocekt_speed_up"),
              (e.Settlement_Win = "Audio/settlement_win"),
              (e.Settlement_Lose = "Audio/settlement_lose"),
              (e.BGM = "Audio/bgm"),
              (e.Turn_Player = "Audio/turn_player"),
              (e.ludo_bg = "Audio/ludo_bg");
          })(n.AudioType || (n.AudioType = {})),
          (function (e) {
            (e.Default = "Default"),
              (e.UnlockSkin = "UnlockSkin"),
              (e.SignDoubleUp = "CheckinDouble"),
              (e.TimingBoxGetReward = "ShowFree"),
              (e.TimingBoxCoins = "ShowFree"),
              (e.TimingBoxDiamond = "ShowFree"),
              (e.ChessOut = "Tokenout"),
              (e.TurntableSpinAgain = "ShowWheelAgain"),
              (e.TurntableDoubleUp = "ShowWheelDouble"),
              (e.ADRewardCoins = "ShowTvrewards"),
              (e.ADRewardDiamond = "ShowTvrewards"),
              (e.UpgradeReward = "ShowLevelup"),
              (e.Game_Over_Insert = "Game_Over_Insert"),
              (e.ShowOlExit = "ShowOlExit_Insert"),
              (e.ShowPcExit = "ShowPcExit_Insert"),
              (e.ShowLocalExit = "ShowLocalExit_Insert"),
              (e.QuitGame_Insert = "QuitGame_Insert"),
              (e.Enter_Foreground_Insert = "Enter_Foreground_Insert"),
              (e.Online_Reward = "Onlinerewards"),
              (e.Task_Reward = "Task_Reward"),
              (e.Shop_Skin_Token = "Shop_Skin_Token"),
              (e.Shop_Skin_Board = "Shop_Skin_Board"),
              (e.Shop_Skin_Dice = "Shop_Skin_Dice"),
              (e.Snakers_Insert = "Snakers_Insert"),
              (e.Get_Gold = "FewCoins"),
              (e.Local_Insert = "LocalPlay_Insert"),
              (e.Guess_Insert = "Guess_Insert"),
              (e.Hall_Quit_Insert = "Menu_Insert"),
              (e.GuessSizeLost = "GuessSizeLost"),
              (e.NewPlayReward = "NewPlayReward"),
              (e.CloseGuessSize_Insert = "Lucky7Exit_Insert"),
              (e.CloseShop_Insert = "StoreExit_Insert"),
              (e.CloseLuckyWheel_Insert = "WheelExit_Insert"),
              (e.CloseWatchAd_Insert = "CloseWatchAd_Insert"),
              (e.ShowUndoDice = "ShowUndo"),
              (e.ShowUndoAgain = "ShowPowerdice"),
              (e.coldSplashShow = "coldSplashShow"),
              (e.OnlinePlay = "OnlinePlay_Insert"),
              (e.ComputerPlay = "ComputerPlay_Insert"),
              (e.LocalPlay = "LocalPlay_Insert"),
              (e.ShowOnlinePlay = "ShowOnlinePlay_Insert"),
              (e.ShowComputerPlay = "ShowComputerPlay_Insert"),
              (e.Activity = "Activity_Insert"),
              (e.ShopSkin = "ShopSkin"),
              (e.SignReward = "SignReward_Insert"),
              (e.FewCoins = "GetGold_Insert");
          })(n.ADType || (n.ADType = {})),
          (function (e) {
            (e[(e.Guest = 0)] = "Guest"),
              (e[(e.Facebook = 1)] = "Facebook"),
              (e[(e.Google = 2)] = "Google");
          })(n.RegisterType || (n.RegisterType = {})),
          (function (e) {
            (e[(e.Coins = 0)] = "Coins"),
              (e[(e.Diamonds = 1)] = "Diamonds"),
              (e[(e.CountReward1 = 2)] = "CountReward1"),
              (e[(e.CountReward2 = 3)] = "CountReward2"),
              (e[(e.CountReward3 = 4)] = "CountReward3");
          })(n.TimingBoxRewardType || (n.TimingBoxRewardType = {})),
          (function (e) {
            (e[(e.Coins = 0)] = "Coins"), (e[(e.Diamonds = 1)] = "Diamonds");
          })(n.ADRewardType || (n.ADRewardType = {})),
          (function (e) {
            (e[(e.Quit = 0)] = "Quit"), (e[(e.OutTime = 1)] = "OutTime");
          })(n.MidwayQuitType || (n.MidwayQuitType = {})),
          (function (e) {
            (e[(e.Turntable = 0)] = "Turntable"),
              (e[(e.TurntableStart = 1)] = "TurntableStart"),
              (e[(e.TurntableSpinAgain = 2)] = "TurntableSpinAgain"),
              (e[(e.TurntableQuit = 3)] = "TurntableQuit"),
              (e[(e.GuessSize = 4)] = "GuessSize"),
              (e[(e.GuessSizeRollDice = 5)] = "GuessSizeRollDice"),
              (e[(e.GuessSizeQuit = 6)] = "GuessSizeQuit"),
              (e[(e.TimingBox = 7)] = "TimingBox"),
              (e[(e.TimingBoxCoins = 8)] = "TimingBoxCoins"),
              (e[(e.TimingBoxDiamonds = 9)] = "TimingBoxDiamonds"),
              (e[(e.TimingBoxQuit = 10)] = "TimingBoxQuit"),
              (e[(e.Shop = 11)] = "Shop"),
              (e[(e.ShopCoins = 12)] = "ShopCoins"),
              (e[(e.ShopDiamonds = 13)] = "ShopDiamonds"),
              (e[(e.ShopSkin = 14)] = "ShopSkin"),
              (e[(e.ShopQuit = 15)] = "ShopQuit"),
              (e[(e.QuitGame = 16)] = "QuitGame"),
              (e[(e.QuitGameYes = 17)] = "QuitGameYes"),
              (e[(e.QuitGameCancel = 18)] = "QuitGameCancel"),
              (e[(e.Sign = 19)] = "Sign"),
              (e[(e.Online = 20)] = "Online"),
              (e[(e.Task = 21)] = "Task"),
              (e[(e.Snakers = 22)] = "Snakers");
          })(n.ButtonClickType || (n.ButtonClickType = {})),
          (function (e) {
            (e.Register = "Register"),
              (e.UserInfo = "UserInfo"),
              (e.Sign = "Sign"),
              (e.TimingBox = "TimingBox"),
              (e.Shop = "Shop"),
              (e.GameType = "GameType"),
              (e.RoomType = "RoomType"),
              (e.EntryCoinsType = "EntryCoinsType"),
              (e.WatchADOut = "WatchADOut"),
              (e.MatchResult = "MatchResult"),
              (e.UseProp = "UseProp"),
              (e.RollDice = "RollDice"),
              (e.Chess = "Chess"),
              (e.GameOverNomarl = "GameOverNomarl"),
              (e.GameOverOther = "GameOverOther"),
              (e.MidwayQuit = "MidwayQuit"),
              (e.CommonClick = "CommonClick"),
              (e.TurntableReward = "TurntableReward"),
              (e.GuessSize = "GuessSize"),
              (e.ADReward = "ADReward"),
              (e.Novice = "Novice"),
              (e.OnlineReward = "OnlineReward"),
              (e.Task = "Task"),
              (e.Skin = "Skin"),
              (e.SnakeGameOverNomarl = "SnakeGameOverNomarl"),
              (e.SnakeMidwayQuit = "SnakeMidwayQuit"),
              (e.GameMod = "GameMod"),
              (e.GameoverMod = "GameoverMod"),
              (e.BeginnersGuide = "BeginnersGuide"),
              (e.BeginnersGuideStep = "BeginnersGuideStep"),
              (e.BeginnersGuideSkip = "BeginnersGuideSkip"),
              (e.StartGameDuration = "StartGameDuration"),
              (e.LocalGameClick = "LocalGameClick"),
              (e.LocalGameTypePlay = "LocalGameTypePlay"),
              (e.LocalGameMidwayQuit = "LocalGameMidwayQuit"),
              (e.LocalGameOver = "LocalGameOver");
          })(n.BuriedPointKey || (n.BuriedPointKey = {})),
          (function (e) {
            (e.isDoubleUp = "isDoubleUp"),
              (e.signDay = "signDay"),
              (e.gameType = "gameType"),
              (e.roomType = "roomType"),
              (e.entryCoins = "entryCoins"),
              (e.result = "result"),
              (e.propType = "propType"),
              (e.gameResult = "gameResult"),
              (e.gameDifficulty = "gameDifficulty"),
              (e.quitType = "quitType"),
              (e.isNovice = "isNovice"),
              (e.clickType = "clickType");
          })(n.BuriedPointSecondKey || (n.BuriedPointSecondKey = {})),
          (function (e) {
            (e.appOpen = "appOpen"),
              (e.newGuideFirstStep = "newGuideFirstStep"),
              (e.newGuideSecondStep = "newGuideSecondStep"),
              (e.newGuideThirdStep = "newGuideThirdStep"),
              (e.newGuideFourthStep = "newGuideFourthStep"),
              (e.newGuideReadyStep = "newGuideReadyStep"),
              (e.enterGameHall = "enterGameHall"),
              (e.openFeatureFromHall = "openFeatureFromHall"),
              (e.onlineGameSelectSreen = "onlineGameSelectSreen"),
              (e.robotGameSelectScreen = "robotGameSelectScreen"),
              (e.localGameSelectScreen = "localGameSelectScreen"),
              (e.onlineGameMatchShow = "onlineGameMatchShow"),
              (e.onlineGameMatchResult = "onlineGameMatchResult"),
              (e.guessSizeRoom = "guessSizeRoom"),
              (e.gameShop = "gameShop"),
              (e.luckyWheel = "luckyWheel"),
              (e.onlineClassicGameRoom = "onlineClassicGameRoom"),
              (e.onlineQuickGameRoom = "onlineQuickGameRoom"),
              (e.robotClassicGameRoom = "robotClassicGameRoom"),
              (e.robotQuickGameRoom = "robotQuickGameRoom"),
              (e.localGameRoom = "localGameRoom"),
              (e.sign = "sign"),
              (e.loadingBegin = "loadingBegin"),
              (e.goldEarnCount = "goldEarnCount"),
              (e.goldCostCount = "goldCostCount"),
              (e.diamondEarnCount = "diamondEarnCount"),
              (e.diamondCostCount = "diamondCostCount"),
              (e.activityIntroduction = "activityIntroduction"),
              (e.activity = "activity"),
              (e.activityGameOver = "activityGameOver"),
              (e.menuActivity = "menuActivity"),
              (e.activityBox = "activityBox");
          })(n.BuriedOneKey || (n.BuriedOneKey = {})),
          (function (e) {
            (e.welecomShow = "welecomShow"),
              (e.welBtnYesClick = "welBtnYesClick"),
              (e.welBtnNoClick = "welBtnNoClick"),
              (e.guideScreenShow = "guideScreenShow"),
              (e.nextBtnClick = "nextBtnClick"),
              (e.skipBtnClick = "skipBtnClick"),
              (e.diceFirstClick = "diceFirstClick"),
              (e.chessFirstClick = "chessFirstClick"),
              (e.nextBtnFirstClick = "nextBtnFirstClick"),
              (e.diceSecondClick = "diceSecondClick"),
              (e.chessSecondClick = "chessSecondClick"),
              (e.nextBtnSecondClick = "nextBtnSecondClick"),
              (e.diceThirdClick = "diceThirdClick"),
              (e.chessThirdClick = "chessThirdClick"),
              (e.nextBtnThirdClick = "nextBtnThirdClick"),
              (e.diceFourthClick = "diceFourthClick"),
              (e.chessFourthClick = "chessFourthClick"),
              (e.okBtnClick = "okBtnClick"),
              (e.fromNewGuide = "fromNewGuide"),
              (e.fromAppOpen = "fromAppOpen"),
              (e.fromOnlineGame = "fromOnlineGame"),
              (e.fromRobotGame = "fromRobotGame"),
              (e.fromLocalGame = "fromLocalGame"),
              (e.fromGuessSizeGame = "fromGuessSizeGame"),
              (e.fromLuckWheel = "fromLuckWheel"),
              (e.openOnlineGame = "openOnlineGame"),
              (e.openRobotGame = "openRobotGame"),
              (e.openLocalGame = "openLocalGame"),
              (e.openGuessGame = "openGuessGame"),
              (e.openShop = "openShop"),
              (e.openLuckWheel = "openLuckWheel"),
              (e.openSettings = "openSettings"),
              (e.openUserInfo = "openUserInfo"),
              (e.openOnlineReward = "openOnlineReward"),
              (e.openDailySign = "openDailySign"),
              (e.openLuckBox = "openLuckBox"),
              (e.coinAddBtnClick = "coinAddBtnClick"),
              (e.selectScreenShow = "selectScreenShow"),
              (e.exitBtnClick = "exitBtnClick"),
              (e.playBtnClick = "playBtnClick"),
              (e.guessSizeRoomShow = "guessSizeRoomShow"),
              (e.rollDiceClick = "rollDiceClick"),
              (e.doubleBtnClick = "doubleBtnClick"),
              (e.rightCount = "rightCount"),
              (e.missCount = "missCount"),
              (e.guideBtnClick = "guideBtnClick"),
              (e.gameShopShow = "gameShopShow"),
              (e.shopSkinId = "shopSkinId"),
              (e.selectSkin = "selectSkin"),
              (e.luckWheelShow = "luckWheelShow"),
              (e.spinBtnClick = "spinBtnClick"),
              (e.spinAgainBtnClick = "spinAgainBtnClick"),
              (e.victoryShow = "victoryShow"),
              (e.victoryBtnClick = "victoryBtnClick"),
              (e.victoryResultShow = "victoryResultShow"),
              (e.enterGameRoom = "enterGameRoom"),
              (e.playerDiceClick = "playerDiceClick"),
              (e.robot1DiceClick = "robot1DiceClick"),
              (e.robot2DiceClick = "robot2DiceClick"),
              (e.robot3DiceClick = "robot3DiceClick"),
              (e.settingBtnClick = "settingBtnClick"),
              (e.openBGM = "openBGM"),
              (e.closeBGM = "closeBGM"),
              (e.openSound = "openSound"),
              (e.closeSound = "closeSound"),
              (e.midwayExit = "midwayExit"),
              (e.gameOver = "gameOver"),
              (e.reviseBtnClick = "reviseBtnClick"),
              (e.againBtnClick = "againBtnClick"),
              (e.backBtnClick = "backBtnClick"),
              (e.modifyBtnClick = "modifyBtnClick"),
              (e.addBtnClick = "addBtnClick"),
              (e.removeBtnClick = "removeBtnClick"),
              (e.position1DiceClick = "position1DiceClick"),
              (e.position2DiceClick = "position2DiceClick"),
              (e.position3DiceClick = "position2DiceClick"),
              (e.position4DiceClick = "position4DiceClick"),
              (e.signDay = "signDay"),
              (e.isDoubleUp = "isDoubleUp"),
              (e.interactBtnClick = "interactBtnClick"),
              (e.sendExpression = "sendExpression"),
              (e.sendSentence = "sendSentence"),
              (e.enterGoldDealScreen = "enterGoldDealScreen"),
              (e.googlePay = "googlePay"),
              (e.vasPay = "vasPay"),
              (e.goldEarnOnline = "goldEarnOnline"),
              (e.goldEarnLucky7 = "goldEarnLucky7"),
              (e.goldEarnWheel = "goldEarnWheel"),
              (e.goldEarnTime = "goldEarnTime"),
              (e.goldEarnInsufficient = "goldEarnInsufficient"),
              (e.goldEarnReward = "goldEarnReward"),
              (e.goldEarnCheckIn = "goldEarnCheckIn"),
              (e.goldEarnBuy = "goldEarnBuy"),
              (e.goldCostOnline = "goldCostOnline"),
              (e.goldCostLucky7 = "goldCostLucky7"),
              (e.diamondEarnTime = "diamondEarnTime"),
              (e.diamondEarnReward = "diamondEarnReward"),
              (e.diamondEarnBuy = "diamondEarnBuy"),
              (e.diamondCostSkin = "diamondCostSkin"),
              (e.activityIntroduction_join = "activityIntroduction_join"),
              (e.activityIntroduction_close = "activityIntroduction_close"),
              (e.activity_play = "activity_play"),
              (e.activity_close = "activity_close"),
              (e.activityGameOver_entrance = "activityGameOver_entrance"),
              (e.menuActivityEntrance_1 = "menuActivityEntrance_1"),
              (e.menuActivityEntrance_2 = "menuActivityEntrance_2");
          })(n.BuriedTwoKey || (n.BuriedTwoKey = {})),
          (function (e) {
            (e.GameDifficulty = "GameDifficulty"),
              (e.GameProps = "GameProps"),
              (e.LevelExp = "upGrade"),
              (e.EntryCoins = "unlockGrade"),
              (e.TimingBoxReward = "giftInfo"),
              (e.Shop = "shopIds"),
              (e.Task = "tasks"),
              (e.Global = "global"),
              (e.Online = "online"),
              (e.ShopSkin = "ShopSkin"),
              (e.snakerAndLadders = "snakerAndLadders"),
              (e.GameInfo = "gameInfo"),
              (e.LeveDifficulty = "LeveDifficulty");
          })(n.CloudControlConfigKey || (n.CloudControlConfigKey = {})),
          (function (e) {
            (e[(e.Win = 0)] = "Win"),
              (e[(e.Lost = 1)] = "Lost"),
              (e[(e.Eate = 2)] = "Eate"),
              (e[(e.beEaten = 3)] = "beEaten");
          })(n.LuckChangeType || (n.LuckChangeType = {})),
          (function (e) {
            (e[(e.Cancel = 0)] = "Cancel"), (e[(e.Yes = 1)] = "Yes");
          })(n.PopupButtonClickType || (n.PopupButtonClickType = {})),
          (function (e) {
            (e[(e.Not = 0)] = "Not"),
              (e[(e.Purchased = 1)] = "Purchased"),
              (e[(e.Experience = 2)] = "Experience");
          })(n.BuyStatus || (n.BuyStatus = {})),
          (function (e) {
            (e[(e.Task_Got = 0)] = "Task_Got"),
              (e[(e.Task_Can = 1)] = "Task_Can"),
              (e[(e.Task_NotCan = 2)] = "Task_NotCan");
          })(n.TaskStatus || (n.TaskStatus = {})),
          (function (e) {
            (e[(e.Task_yellow = 1)] = "Task_yellow"),
              (e[(e.Task_blue = 2)] = "Task_blue");
          })(n.TaskQuality || (n.TaskQuality = {})),
          (function (e) {
            (e[(e.Task_Win = 1)] = "Task_Win"),
              (e[(e.Task_end_point = 2)] = "Task_end_point"),
              (e[(e.Task_six = 3)] = "Task_six"),
              (e[(e.Task_attack = 4)] = "Task_attack"),
              (e[(e.Task_complete = 5)] = "Task_complete"),
              (e[(e.Task_luck = 6)] = "Task_luck"),
              (e[(e.Task_win_luck = 7)] = "Task_win_luck"),
              (e[(e.Task_turntable = 8)] = "Task_turntable"),
              (e[(e.Task_free_coins = 9)] = "Task_free_coins"),
              (e[(e.Task_free_diamonds = 10)] = "Task_free_diamonds"),
              (e[(e.Task_dice = 11)] = "Task_dice");
          })(n.TaskType || (n.TaskType = {})),
          (function (e) {
            (e[(e.Gold = 1)] = "Gold"),
              (e[(e.Diamonds = 2)] = "Diamonds"),
              (e[(e.Skin_Experience = 3)] = "Skin_Experience");
          })(n.GoldType || (n.GoldType = {})),
          (function (e) {
            (e[(e.Token = 1)] = "Token"),
              (e[(e.Dice = 2)] = "Dice"),
              (e[(e.Board = 3)] = "Board");
          })(n.SkinType || (n.SkinType = {})),
          (function (e) {
            (e[(e.English = 1)] = "English"),
              (e[(e.Arabic = 2)] = "Arabic"),
              (e[(e.Hindi = 3)] = "Hindi"),
              (e[(e.Urdu = 4)] = "Urdu");
          })(n.LanguageType || (n.LanguageType = {})),
          (function (e) {
            (e[(e.Activity = 1)] = "Activity"), (e[(e.Room = 2)] = "Room");
          })(n.Entrance || (n.Entrance = {})),
          (function (e) {
            (e[(e.cup = 1)] = "cup"), (e[(e.roadblock = 2)] = "roadblock");
          })(n.circulateActivity || (n.circulateActivity = {})),
          (function (e) {
            (e[(e.unopened = 0)] = "unopened"),
              (e[(e.today = 1)] = "today"),
              (e[(e.progress = 2)] = "progress"),
              (e[(e.end = 3)] = "end"),
              (e[(e.delete = 4)] = "delete");
          })(n.activityState || (n.activityState = {})),
          (function (e) {
            (e[(e.free = 0)] = "free"),
              (e[(e.shop = 1)] = "shop"),
              (e[(e.boxActivity = 2)] = "boxActivity"),
              (e[(e.debris = 3)] = "debris"),
              (e[(e.expire = 4)] = "expire"),
              (e[(e.gift = 5)] = "gift");
          })(n.SkinGetType || (n.SkinGetType = {})),
          (function (e) {
            (e[(e.UndoDice = 10001)] = "UndoDice"),
              (e[(e.Shield = 10002)] = "Shield"),
              (e[(e.Basic = 10003)] = "Basic"),
              (e[(e.Rare = 10004)] = "Rare"),
              (e[(e.Epic = 10005)] = "Epic"),
              (e[(e.Gold = 10006)] = "Gold"),
              (e[(e.Diamond = 10007)] = "Diamond"),
              (e[(e.SkinDebris = 10008)] = "SkinDebris"),
              (e[(e.DiceDebris = 10009)] = "DiceDebris"),
              (e[(e.TokenDebris = 10010)] = "TokenDebris"),
              (e[(e.MaxReward = 10011)] = "MaxReward"),
              (e[(e.Medal = 10012)] = "Medal"),
              (e[(e.Bomb = 10013)] = "Bomb"),
              (e[(e.ShopSkin = 10014)] = "ShopSkin"),
              (e[(e.HeadFrame = 10015)] = "HeadFrame"),
              (e[(e.Head = 10016)] = "Head"),
              (e[(e.MonoplyDice = 10017)] = "MonoplyDice");
          })(n.Item || (n.Item = {})),
          cc._RF.pop();
      },
      {},
    ],
    GameMatch: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "48064EIlqFASZfjWvV7IEph", "GameMatch");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Manager/RoomInfoManager"),
          c = cc._decorator,
          l = c.ccclass,
          u = c.property,
          d = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_bg = null),
                (t.labMyGold = null),
                (t.chessNode = null),
                (t.playerInfoNode = null),
                (t._colorList = ["lan", "hong", "lv", "huang"]),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.onUpdateGoldNum();
              }),
              (t.prototype.onUpdateGoldNum = function () {
                var e = s.default.getInstance().getPlayerWinGold();
                this.labMyGold.string = e.first.toString();
              }),
              i([u(cc.Sprite)], t.prototype, "img_bg", void 0),
              i([u(cc.Label)], t.prototype, "labMyGold", void 0),
              i([u(cc.Node)], t.prototype, "chessNode", void 0),
              i([u(cc.Node)], t.prototype, "playerInfoNode", void 0),
              i([l], t)
            );
          })(r.default);
        (n.default = d), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
      },
    ],
    GameScene: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "68d18hulKlLK4cTScn8resv", "GameScene");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/ChessManager"),
          p = e("../Framework/Manager/GameDataManager"),
          f = e("../Framework/Manager/LuckManager"),
          h = e("../Framework/Manager/MapGridManager"),
          g = e("../Framework/Manager/RobotManager"),
          m = e("../Framework/Manager/RoomInfoManager"),
          _ = e("../Framework/Manager/ShopDataManager"),
          y = e("../Framework/Manager/UserInfoManager"),
          v = e("../Framework/Native/NativeBridge"),
          I = e("../Framework/Utils/Utils"),
          C = e("./Chess"),
          k = e("./GameSettlementView"),
          w = e("./MapGrid"),
          P = e("./PlayerInfo"),
          S = e("./QuitPrizeView"),
          b = e("./UsePropsView"),
          T = cc._decorator,
          M = T.ccclass,
          R = T.property,
          G = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labTurnPlayerIndex = null),
                (t.labDicePoints = null),
                (t.mapGridNode = null),
                (t.chessNode = null),
                (t.mapNode = null),
                (t.playerInfoNode = null),
                (t.topNode = null),
                (t.sprChessBaseBgs = []),
                (t.playerInfoNodes = []),
                (t.terminalAnimNodes = []),
                (t.spfGameModes = []),
                (t.nodeUseProps = null),
                (t.usePropsViewPrefab = null),
                (t.mapGridPrefab = null),
                (t.chessPrefab = null),
                (t.playerInfoPrefab = null),
                (t.sprCenter = null),
                (t.mainNode = null),
                (t.mainNodeScale = 0),
                (t.labGameDifficulty = null),
                (t.nodeDiceTestUI = null),
                (t.node_terminal = null),
                (t.img_center = null),
                (t.node_base = null),
                (t.classice_guide = null),
                (t.quick_guide = null),
                (t.safe_Node = null),
                (t.guide_node = null),
                (t.node_undo = null),
                (t.undo_list = []),
                (t.undo_guide = null),
                (t.quickGuide = null),
                (t.classiceGuide = null),
                (t.node_bian = null),
                (t.node_player = null),
                (t._isshowTestUIUI = !1),
                (t._mapGridCount = 76),
                (t._turnPlayerIndex = -1),
                (t._playerIndexs = []),
                (t._barrierGrids = []),
                (t._arriveTerminalPointCount = 0),
                (t._playerInfos = []),
                (t._winUsers = []),
                (t._winPlay = []),
                (t._removePlayerIndexs = []),
                (t._curLevel = 0),
                (t._usePropsView = null),
                (t._isFirstRank = !1),
                (t._timestamp = 0),
                (t._checkNet = 30),
                (t._checkTime = 0),
                (t._colorList = ["lan", "hong", "lv", "huang"]),
                (t._isShowExpression = !1),
                (t._guideParam = null),
                (t._undoIndex = 0),
                (t.gameMode = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                var e = this;
                I.default.localStr(this.node),
                  (this.gameMode = m.default.getInstance().getGameMode()),
                  y.default.getInstance().isShowAppluck(!0),
                  y.default.getInstance().deductEntryGold(),
                  y.default.getInstance().addGameTotalRounds(),
                  p.default.getInstance().setOpenAppPlayGameCount(),
                  y.default
                    .getInstance()
                    .setGameCount(y.default.getInstance().getGameCount() + 1),
                  1 == I.default.getRandomNum(1, 2)
                    ? g.default.getInstance().randomSendExpression()
                    : g.default.getInstance().randomSendSentence(),
                  p.default.getInstance().setWinGoldQuit(0),
                  p.default.getInstance().setSceneType(c.SceneType.Game),
                  this.registerAllEvents(),
                  this.initMyInfo(),
                  (this._timestamp = I.default.getCurTimeStamp());
                var t = m.default.getInstance().getRoomMode();
                d.default.getInstance().setPlayerChessColors(),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: I.default.getEventName(),
                      actionName: c.BuriedTwoKey.enterGameRoom,
                    }),
                  m.default.getInstance().getChessColor();
                for (
                  var n = _.default.getInstance().getSelectBoard(),
                    o =
                      (s.SKIN_PICTURE_PATH,
                      [
                        "original",
                        "grass",
                        "sandbeach",
                        "snow",
                        "space",
                        "Indiastyle",
                        "food",
                      ].indexOf(n),
                      0);
                  o < this.sprChessBaseBgs.length;
                  o++
                ) {
                  var a = d.default.getInstance().getPlayerChessColor(o),
                    i =
                      s.SKIN_PICTURE_PATH +
                      n +
                      "_img_base_bg_" +
                      this._colorList[a];
                  this.setSpfsRes(this.sprChessBaseBgs[o], i);
                }
                "grass" == n || "original" == n
                  ? ((this.node_terminal.node.active = !1),
                    (this.node_bian.active = "original" == n))
                  : ((this.node_terminal.node.active = !0),
                    this.loadRes(
                      s.SKIN_PICTURE_PATH + n + "_img_terminal_point",
                      cc.SpriteFrame,
                      function (t) {
                        e.node_terminal.spriteFrame = t;
                      }
                    )),
                  (this.img_center.node.active = "sandbeach" == n),
                  l.default
                    .getInstance()
                    .playMusicWithPath(c.AudioType.ludo_bg, !0, 1),
                  y.default.getInstance().setGameSettingInfo(!1, !0),
                  l.default.getInstance().setMusicOpen(!1);
                var r = p.default.getInstance().getTools().getSkinInfo();
                for (
                  s.GAME_PREFAB_PATH, r.skinName, o = 0;
                  o < this._mapGridCount;
                  o++
                ) {
                  var f = this.mapGridNode.getChildByName("mapGrid_" + o),
                    C = cc.instantiate(this.mapGridPrefab);
                  (C.position = f.position),
                    (C.parent = this.mapGridNode),
                    (C.zIndex = this._mapGridCount - o);
                  var k = C.getComponent(w.default),
                    P = h.default.getInstance().isSafeGrid(o),
                    S = h.default.getInstance().isBarrierGrid(o),
                    T = h.default.getInstance().isIndicationGrid(o),
                    M = h.default.getInstance().isColorGrid(o);
                  if (M == s.ARRAY_ELE_NOT_EXIST)
                    h.default.getInstance().addMapGrid(k, o, P, S, T);
                  else {
                    var R = d.default.getInstance().getPlayerChessColor(M);
                    h.default.getInstance().addMapGrid(k, o, P, S, T, R);
                  }
                  S && this._barrierGrids.push(k);
                }
                var G =
                  m.default.getInstance().getRoomMode() == c.GameRoomMode.Quick;
                for (o = 0; o < 4; o++)
                  h.default.getInstance().setBarrierStatus(o, G),
                    G || this._barrierGrids[o].hideBarrier();
                var A = cc.instantiate(this.usePropsViewPrefab);
                (A.parent = this.nodeUseProps),
                  this.gameMode == c.GameMode.Local && (A.active = !1),
                  (this._usePropsView = A.getComponent(b.default)),
                  this.gameMode == c.GameMode.Computer ||
                  this.gameMode == c.GameMode.Online ||
                  this.gameMode == c.GameMode.BombItem ||
                  this.gameMode == c.GameMode.Roadblock
                    ? this.loadOnlineComputer()
                    : ((this.node_player.active = !0), this.loadLocal()),
                  this.showTestUI(!1),
                  t == c.GameRoomMode.Quick
                    ? this.scheduleOnce(function () {
                        e.turnPlayerOperation();
                      }, 1)
                    : (c.GameRoomMode.Classic,
                      this.scheduleOnce(function () {
                        e.turnPlayerOperation();
                      }, 1)),
                  I.default.getUINeedScale() &&
                    (this.mainNode.scale = this.mainNodeScale.valueOf()),
                  m.default.getInstance().getPlayerCount() ==
                    c.PlayerCount.Two && (this.mapNode.y += 100),
                  (this.labGameDifficulty.node.active = !1),
                  p.default.getInstance().getTools().getGlobalJson().info[0]
                    .show_game_banner && v.default.showBanner(),
                  (p.default.getInstance().isWin = !1);
              }),
              (t.prototype.loadOnlineComputer = function () {
                !y.default.getInstance().getClassiceGuide() ||
                (m.default.getInstance().getRoomMode() !=
                  c.GameRoomMode.Classic &&
                  m.default.getInstance().getComputerRoomMode() !=
                    c.GameRoomMode.Classic) ||
                this.gameMode == c.GameMode.BombItem ||
                this.gameMode == c.GameMode.Roadblock
                  ? (this.classiceGuide.active = !1)
                  : ((this.classiceGuide.active = !0),
                    y.default.getInstance().setClassiceGuide()),
                  !y.default.getInstance().getQuickGuide() ||
                  (m.default.getInstance().getRoomMode() !=
                    c.GameRoomMode.Quick &&
                    m.default.getInstance().getComputerRoomMode() !=
                      c.GameRoomMode.Quick) ||
                  this.gameMode == c.GameMode.BombItem ||
                  this.gameMode == c.GameMode.Roadblock
                    ? (this.quickGuide.active = !1)
                    : ((this.quickGuide.active = !0),
                      y.default.getInstance().setQuickGuide());
                for (var e = 0; e < 4; e++)
                  for (
                    var t = e,
                      n = this.playerIsRobot(t),
                      o = d.default.getInstance().getPlayerChessColor(t),
                      a = 0;
                    a < s.PLAYER_CHESS_COUNT;
                    a++
                  ) {
                    var i = a,
                      r = this.chessNode.getChildByName("chess_" + t + "_" + i);
                    ((h = cc.instantiate(this.chessPrefab)).position =
                      r.position),
                      (h.parent = this.chessNode);
                    var l = h.getComponent(C.default);
                    d.default
                      .getInstance()
                      .addPlayerChess(t, l, i, o, n, "original"),
                      m.default.getInstance().getPlayerCount() ==
                        c.PlayerCount.Two &&
                        (t == c.PlayerIndex.LeftBottom ||
                        t == c.PlayerIndex.RightTop
                          ? (h.active = !0)
                          : (h.active = !1));
                  }
                var u = [],
                  f = y.default.getInstance().getAllUser();
                for (e = 0; e < f.length; e++) {
                  var h;
                  (t = f[e].getPlayerIndex()),
                    ((h = cc.instantiate(this.playerInfoPrefab)).position =
                      this.playerInfoNodes[t].position),
                    (h.parent = this.playerInfoNodes[t].parent);
                  var g = h.getComponent(P.default);
                  g.setInfo(f[e], this._usePropsView),
                    (this._playerInfos[t] = g),
                    this._playerIndexs.push(t),
                    (u[t] = h);
                }
                var _ = 0,
                  v = 0;
                this.gameMode == c.GameMode.Computer
                  ? m.default.getInstance().getComputerRoomMode() ==
                      c.GameRoomMode.Quick && ((_ = 2), (v = 2))
                  : m.default.getInstance().getRoomMode() ==
                      c.GameRoomMode.Quick && ((_ = 2), (v = 2)),
                  p.default.getInstance().isWatchADOut() &&
                    (p.default.getInstance().setWatchADOut(!1), (v += 1));
                var I = y.default.getInstance().getMyselfUserInfo();
                for (e = 0; e < this._playerIndexs.length; e++)
                  I.getPlayerIndex() == this._playerIndexs[e]
                    ? v > 0 &&
                      d.default
                        .getInstance()
                        .setPlayerChessToStartPosition(this._playerIndexs[e], v)
                    : _ > 0 &&
                      d.default
                        .getInstance()
                        .setPlayerChessToStartPosition(
                          this._playerIndexs[e],
                          _
                        );
              }),
              (t.prototype.loadLocal = function () {
                for (
                  var e = p.default.getInstance().getLocalInfo(), t = 0;
                  t < 4;
                  t++
                ) {
                  var n = t,
                    o = e[t],
                    a = !1;
                  o && o.isComputer && (a = !0);
                  for (
                    var i = d.default.getInstance().getPlayerChessColor(n),
                      r = 0;
                    r < s.PLAYER_CHESS_COUNT;
                    r++
                  ) {
                    var c = r,
                      l = this.chessNode.getChildByName("chess_" + n + "_" + c);
                    ((h = cc.instantiate(this.chessPrefab)).position =
                      l.position),
                      (h.parent = this.chessNode);
                    var u = h.getComponent(C.default);
                    d.default
                      .getInstance()
                      .addPlayerChess(n, u, c, i, a, "original"),
                      (h.active = !!o);
                  }
                }
                var f = y.default.getInstance().getLocalAllUser();
                for (t = 0; t < f.length; t++) {
                  var h;
                  (n = f[t].getPlayerIndex()),
                    ((h = cc.instantiate(this.playerInfoPrefab)).name =
                      "playerInfo_" + n),
                    (h.position = this.playerInfoNodes[n].position),
                    (h.parent = this.playerInfoNodes[n].parent);
                  var g = h.getComponent(P.default);
                  g.setInfo(f[t], this._usePropsView),
                    (this._playerInfos[n] = g),
                    this._playerIndexs.push(n);
                }
                var m = y.default.getInstance().getMyselfUserInfo();
                for (t = 0; t < this._playerIndexs.length; t++)
                  m.getPlayerIndex(), this._playerIndexs[t];
              }),
              (t.prototype.addPlayerIndexChess = function (e) {
                y.default.getInstance().addPlayer(e);
                for (
                  var t = y.default.getInstance().getLocalAllUser(), n = 0;
                  n < s.PLAYER_CHESS_COUNT;
                  n++
                ) {
                  var o = n,
                    a = this.chessNode.getChildByName("chess_" + e + "_" + o);
                  d.default.getInstance().addChess(e, o, a.position);
                }
                var i = null;
                for (var r in t) t[r].getPlayerIndex() == e && (i = t[r]);
                var c = this.playerInfoNodes[e].parent.getChildByName(
                  "playerInfo_" + e
                );
                if (c) c.active = !0;
                else {
                  var l = cc.instantiate(this.playerInfoPrefab);
                  (l.name = "playerInfo_" + e),
                    (l.position = this.playerInfoNodes[e].position),
                    (l.parent = this.playerInfoNodes[e].parent);
                  var u = l.getComponent(P.default);
                  u.setInfo(i, this._usePropsView), (this._playerInfos[e] = u);
                }
                this._playerIndexs.push(e),
                  this._playerIndexs.sort(function (e, t) {
                    return e - t;
                  });
              }),
              (t.prototype.delPlayerIndexChess = function (e) {
                y.default.getInstance().delPlayer(e),
                  d.default.getInstance().delectChess(e),
                  (this.playerInfoNodes[e].parent.getChildByName(
                    "playerInfo_" + e
                  ).active = !1);
                var t = this.getPlayerIndex(e);
                this.removePlayerIndex(e),
                  e == this._turnPlayerIndex && this.turnPlayerOperation(t);
              }),
              (t.prototype.getPlayerIndex = function (e) {
                var t = 0;
                if (-1 != this._playerIndexs.indexOf(e)) {
                  var n = this._playerIndexs.indexOf(e);
                  n + 1 < this._playerIndexs.length &&
                    (t = this._playerIndexs[n + 1]);
                }
                return t;
              }),
              (t.prototype.setSpfsRes = function (e, t) {
                this.loadRes(t, cc.SpriteFrame, function (t) {
                  e.spriteFrame = t;
                });
              }),
              (t.prototype.start = function () {
                this.schedule(this.showNoNetWork, 1);
              }),
              (t.prototype.showNoNetWork = function () {
                this._checkTime++,
                  y.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getPlayerIndex() != this._turnPlayerIndex &&
                    this._checkTime >= this._checkNet &&
                    v.default.getNetworkStatus() == c.NetworkStatus.No &&
                    (this.checkPopupNoNetwork(), (this._checkTime = 0));
              }),
              (t.prototype.checkPopupNoNetwork = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "NoNetworkView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node;
                  }
                );
              }),
              (t.prototype.playerIsRobot = function (e) {
                var t = y.default.getInstance().getAllUser(),
                  n = p.default.getInstance().getLocalInfo();
                if (this.gameMode == c.GameMode.Local) return n[e].isComputer;
                for (var o = 0; o < t.length; o++)
                  if (t[o].getPlayerIndex() == e) return t[o].isRobot();
                return !1;
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Remove_Barrier,
                  this.onRemoveBarrier,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Player_Operation_Completed,
                    this.onPlayerOptCompleted,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Roll_The_Dice,
                    this.onRollTheDice,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Game_Over,
                    this.gameOver,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.FirstRank_Back_To_Hall,
                    this.onFirstRankBackToHall,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Player_Walk_Start,
                    this.onWalkStart,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Bakc_To_Hall,
                    this.onBackToHall,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Hide_Dice_TestUI,
                    this.hideTestUI,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Roll_The_Dice_AI,
                    this.rollDiceAI,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Win_Player_Flag,
                    this.showWinPlayerFlag,
                    this
                  ),
                  this.registerEvent(c.GameEvent.Game_Load, this.onLoad, this),
                  this.registerEvent(
                    c.GameEvent.Play_Close_Audio,
                    this.onCloseAudio,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Add_Player,
                    this.addPlayerIndexChess,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Del_Player,
                    this.delPlayerIndexChess,
                    this
                  ),
                  this.registerEvent(c.GameEvent.eatChess, this.eatChess, this),
                  this.registerEvent(
                    c.GameEvent.send_Expression,
                    this.showExpression,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Guide,
                    this.showGuide,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Guide_Safe,
                    this.showSafeGuide,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Close_Guide_Ui,
                    this.closeGuide,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Undo_Node,
                    this.onBtnShowUndoClick,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Undo_Help,
                    this.showUndoHelp,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Undo_Dice,
                    this.showUndoDice,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Quit_Prize_View,
                    this.onShowQuitPrizeView,
                    this
                  );
              }),
              (t.prototype.eatChess = function () {
                (this.chessNode.zIndex = 2),
                  (this.playerInfoNode.zIndex = 1),
                  (this.guide_node.zIndex = 0);
              }),
              (t.prototype.showExpression = function () {
                (this.chessNode.zIndex = 1),
                  (this.playerInfoNode.zIndex = 2),
                  (this.guide_node.zIndex = 0);
              }),
              (t.prototype.onCloseAudio = function () {
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click);
              }),
              (t.prototype.initMyInfo = function () {
                var e = y.default.getInstance().getMyselfUserInfo();
                this._curLevel = e.getLevel();
              }),
              (t.prototype.onPlayerOptCompleted = function (e, t, n) {
                if (this.checkGameOver(e)) this.gameOver();
                else if (t) this.turnPlayerOperation(e);
                else if (n) {
                  for (
                    var o = d.default.getInstance().getPlayerAllChess(e),
                      a = 0,
                      i = 0;
                    i < o.length;
                    i++
                  )
                    o[i].isArriveTerminalPoint() && (a += 1);
                  this.gameMode != c.GameMode.BombItem &&
                    this.gameMode != c.GameMode.Roadblock &&
                    (a != s.PLAYER_CHESS_COUNT
                      ? this.turnPlayerOperation(e)
                      : this.turnPlayerOperation());
                } else this.turnPlayerOperation();
              }),
              (t.prototype.setTurnPlayerIndex = function (e) {
                if (null != e) this._turnPlayerIndex = e;
                else if (-1 == this._turnPlayerIndex) {
                  var t = I.default.getRandomNum(
                    0,
                    this._playerIndexs.length - 1
                  );
                  this._turnPlayerIndex = this._playerIndexs[t];
                } else if (
                  p.default.getInstance().getDicePoints() == s.DICE_MAX_POINTS
                )
                  this._turnPlayerIndex = this._turnPlayerIndex;
                else {
                  for (var n = -1, o = 0; o < this._playerIndexs.length; o++)
                    if (this._turnPlayerIndex == this._playerIndexs[o]) {
                      n = o;
                      break;
                    }
                  -1 != n
                    ? n == this._playerIndexs.length - 1
                      ? (this._turnPlayerIndex = this._playerIndexs[0])
                      : (this._turnPlayerIndex = this._playerIndexs[n + 1])
                    : cc.log(
                        "setTurnPlayerIndex error, index:" +
                          n +
                          ",turnPlayerIndex:" +
                          e
                      );
                }
              }),
              (t.prototype.checkRemovePlayerIndexs = function () {
                if (this._removePlayerIndexs.length > 0)
                  for (var e = 0; e < this._removePlayerIndexs.length; e++)
                    this.removePlayerIndex(this._removePlayerIndexs[e]),
                      this._removePlayerIndexs.splice(e, 1);
              }),
              (t.prototype.turnPlayerOperation = function (e) {
                this.setTurnPlayerIndex(e),
                  (this.labTurnPlayerIndex.string =
                    "\u5f53\u524d\u64cd\u4f5c\u73a9\u5bb6\u7d22\u5f15:" +
                    this._turnPlayerIndex),
                  cc.log(
                    "\u5f53\u524d\u64cd\u4f5c\u7684\u73a9\u5bb6\u7d22\u5f15:" +
                      this._turnPlayerIndex
                  ),
                  cc.director.emit(
                    c.GameEvent.Turn_Player_Operation,
                    this._turnPlayerIndex
                  ),
                  this.checkRemovePlayerIndexs(),
                  this.showTestUI(
                    this._turnPlayerIndex == c.PlayerIndex.LeftBottom
                  );
              }),
              (t.prototype.saveWinUser = function (e) {
                var t = y.default.getInstance().getAllUser();
                this.gameMode == c.GameMode.Local &&
                  (t = y.default.getInstance().getLocalAllUser());
                for (var n = 0; n < t.length; n++)
                  e == t[n].getPlayerIndex() && this._winUsers.push(t[n]);
              }),
              (t.prototype.checkGameOver = function (e) {
                for (
                  var t = d.default.getInstance().getPlayerAllChess(e),
                    n = 0,
                    o = 0;
                  o < t.length;
                  o++
                )
                  t[o].isArriveTerminalPoint() && (n += 1);
                if (!(n > 0)) return !1;
                if (this.gameMode == c.GameMode.Local) {
                  var a = p.default.getInstance().getLocalInfo(),
                    i = 0;
                  for (var o in a) a[o] && i++;
                  if (i <= 3)
                    return !(
                      n != s.PLAYER_CHESS_COUNT || (this.saveWinUser(e), 0)
                    );
                  if (n == s.PLAYER_CHESS_COUNT) {
                    this.saveWinUser(e),
                      (this._arriveTerminalPointCount += 1),
                      this._removePlayerIndexs.push(e);
                    var r = this.getPlayerIndex(e);
                    return (
                      e == this._turnPlayerIndex && this.turnPlayerOperation(r),
                      2 == this._arriveTerminalPointCount
                    );
                  }
                  return !1;
                }
                if (
                  (this.gameMode == c.GameMode.BombItem ||
                    this.gameMode == c.GameMode.Roadblock) &&
                  1 == n
                )
                  return (
                    -1 == this._winPlay.indexOf(e) &&
                      (this.saveWinUser(e),
                      (this._arriveTerminalPointCount += 1),
                      this._winPlay.push(e)),
                    1 == this._arriveTerminalPointCount ||
                      (e ==
                        y.default
                          .getInstance()
                          .getMyselfUserInfo()
                          .getPlayerIndex() && (this._isFirstRank = !0),
                      this.showWinPlayerFlag(e),
                      this._removePlayerIndexs.push(e),
                      (i = this.getPlayerIndex(e)),
                      e == this._turnPlayerIndex && this.turnPlayerOperation(i),
                      !1)
                  );
                if (
                  m.default.getInstance().getRoomMode() ==
                    c.GameRoomMode.Classic ||
                  m.default.getInstance().getComputerRoomMode() ==
                    c.GameRoomMode.Classic
                ) {
                  if (
                    m.default.getInstance().getPlayerCount() ==
                    c.PlayerCount.Two
                  )
                    return !(
                      n != s.PLAYER_CHESS_COUNT || (this.saveWinUser(e), 0)
                    );
                  if (
                    m.default.getInstance().getPlayerCount() ==
                    c.PlayerCount.Four
                  )
                    return !(
                      n != s.PLAYER_CHESS_COUNT ||
                      (this.saveWinUser(e),
                      (this._arriveTerminalPointCount += 1),
                      2 != this._arriveTerminalPointCount &&
                        (e ==
                          y.default
                            .getInstance()
                            .getMyselfUserInfo()
                            .getPlayerIndex() && (this._isFirstRank = !0),
                        this.showWinPlayerFlag(e),
                        this._removePlayerIndexs.push(e),
                        1))
                    );
                } else if (
                  m.default.getInstance().getRoomMode() ==
                    c.GameRoomMode.Quick ||
                  m.default.getInstance().getComputerRoomMode() ==
                    c.GameRoomMode.Quick
                )
                  return !(1 != n || (this.saveWinUser(e), 0));
              }),
              (t.prototype.removePlayerIndex = function (e) {
                for (var t = 0; t < this._playerIndexs.length; t++)
                  if (this._playerIndexs[t] == e) {
                    this._playerIndexs.splice(t, 1);
                    break;
                  }
              }),
              (t.prototype.onWalkStart = function (e) {
                e ==
                  y.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getPlayerIndex() && this.closePlayerCD(e);
              }),
              (t.prototype.gameOver = function (e) {
                var t = this;
                if ((void 0 === e && (e = !1), e))
                  this.onBackToHall(c.MidwayQuitType.OutTime);
                else {
                  for (var n in this._playerInfos)
                    this.closePlayerCD(parseInt(n));
                  this.scheduleOnce(function () {
                    t.showGameSettlement();
                  }, 1);
                }
              }),
              (t.prototype.checkUserIsWin = function (e) {
                for (var t = 0; t < this._winUsers.length; t++)
                  if (e == this._winUsers[t].getUserId()) return !0;
                return !1;
              }),
              (t.prototype.getUserSettlementInfos = function () {
                for (
                  var e = m.default.getInstance().getPlayerWinGold(),
                    t = m.default.getInstance().getPlayerGetExp(),
                    n = [],
                    o = 0;
                  o < this._winUsers.length;
                  o++
                )
                  ((i = {}).userInfo = this._winUsers[o]),
                    (i.isWin = !0),
                    (i.winGold = 0 == o ? e.first : e.second),
                    (i.getExp = t.winExp),
                    n.push(i);
                var a = y.default.getInstance().getAllUser();
                for (
                  this.gameMode == c.GameMode.Local &&
                    (a = y.default.getInstance().getLocalAllUser()),
                    o = 0;
                  o < a.length;
                  o++
                ) {
                  var i;
                  this.checkUserIsWin(a[o].getUserId()) ||
                    (((i = {}).userInfo = a[o]),
                    (i.isWin = !1),
                    (i.winGold = 0),
                    (i.getExp = t.lostExp),
                    n.push(i));
                }
                return n;
              }),
              (t.prototype.refreshGameResult = function (e) {
                y.default
                  .getInstance()
                  .setGameDifficultyInfo(
                    null,
                    e ? c.GameResult.Success : c.GameResult.Fail
                  );
              }),
              (t.prototype.showGameSettlement = function () {
                var e = this;
                if (0 != this._winUsers.length) {
                  var t = this.node.getChildByName("FirstRankQuitView");
                  t && t.destroy();
                  var n = y.default.getInstance().getMyselfUserInfo(),
                    o = this.checkUserIsWin(n.getUserId());
                  if (
                    (u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameoverMod,
                        gameMode: this.gameMode,
                        GameRoomMode: m.default.getInstance().getRoomMode(),
                        playerCount: m.default.getInstance().getPlayerCount(),
                        win: o ? 1 : 0,
                      }),
                    this.gameMode == c.GameMode.Local)
                  ) {
                    var a = {
                      totalGameCount: y.default
                        .getInstance()
                        .getGameTotalRounds(),
                      gameCount: p.default
                        .getInstance()
                        .getOpenAppPlayGameCount(),
                      gameDuration: this.getDurationTime(),
                    };
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.localGameRoom,
                        actionName: c.BuriedTwoKey.gameOver,
                        value: a,
                      });
                  } else
                    (a = {
                      totalGameCount: y.default
                        .getInstance()
                        .getGameTotalRounds(),
                      gameCount: p.default
                        .getInstance()
                        .getOpenAppPlayGameCount(),
                      gameDuration: this.getDurationTime(),
                      gameResult: o,
                      playerFirstDice6Num: p.default
                        .getInstance()
                        .getFirstSixIndex(),
                      playerStepChessCount: p.default
                        .getInstance()
                        .getEatOther(),
                      playerStepedChessCount: p.default
                        .getInstance()
                        .getMyBeEatenOther(),
                      playerFirstTimeStepDura: p.default
                        .getInstance()
                        .getFirstEatChessTime(),
                      undoCount: p.default.getInstance().getUndoCount(),
                    }),
                      u.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: I.default.getEventName(),
                          actionName: c.BuriedTwoKey.gameOver,
                          value: a,
                        });
                  this.loadRes(
                    s.GAME_PREFAB_PATH + "GameSettlementView",
                    cc.Prefab,
                    function (t) {
                      var o = cc.instantiate(t);
                      o.parent = e.node;
                      var a = o.getComponent(k.default),
                        i = e.checkUserIsWin(n.getUserId());
                      i && y.default.getInstance().addWinRounds();
                      for (
                        var r = e.getUserSettlementInfos(), s = 0, l = 0;
                        l < r.length;
                        l++
                      ) {
                        var d = r[l],
                          p = d.userInfo,
                          h = p.getGoldNum();
                        (h += d.winGold),
                          p.setGoldNum(h),
                          (e.gameMode == c.GameMode.BombItem &&
                            e.gameMode == c.GameMode.Roadblock) ||
                            p.setExp(p.getExp() + d.getExp),
                          p.isMyself() &&
                            ((s = d.getExp),
                            d.winGold &&
                              u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedOneKey.goldEarnCount,
                                  actionName: c.BuriedTwoKey.goldEarnOnline,
                                  value: d.winGold,
                                }));
                      }
                      a.setInfo(i, s, r),
                        e.reportGameOverInfo(i),
                        e.gameMode != c.GameMode.Local &&
                          f.default
                            .getInstance()
                            .changeLuck(
                              n.getPlayerIndex(),
                              i ? c.LuckChangeType.Win : c.LuckChangeType.Lost
                            );
                    }
                  );
                }
              }),
              (t.prototype.reportGameOverInfo = function (e) {
                m.default.getInstance().getRoomMode() ==
                  c.GameRoomMode.Classic &&
                m.default.getInstance().getPlayerCount() == c.PlayerCount.Four
                  ? (u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverOther,
                        gameResult: e
                          ? c.GameResult.Success
                          : c.GameResult.Fail,
                        usePropCount: this._usePropsView.getUsePropsInfo(),
                        gameDifficulty: m.default
                          .getInstance()
                          .getGameDifficulty(),
                        isAdvanceQuit: !1,
                        duration: this.getDurationTime(),
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverOther,
                        actionName: c.BuriedPointSecondKey.gameResult,
                        value: e ? c.GameResult.Success : c.GameResult.Fail,
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverOther,
                        actionName: c.BuriedPointSecondKey.gameDifficulty,
                        value: m.default.getInstance().getGameDifficulty(),
                      }))
                  : (u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverNomarl,
                        gameResult: e
                          ? c.GameResult.Success
                          : c.GameResult.Fail,
                        usePropCount: this._usePropsView.getUsePropsInfo(),
                        gameDifficulty: m.default
                          .getInstance()
                          .getGameDifficulty(),
                        duration: this.getDurationTime(),
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverNomarl,
                        actionName: c.BuriedPointSecondKey.gameResult,
                        value: e ? c.GameResult.Success : c.GameResult.Fail,
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.GameOverNomarl,
                        actionName: c.BuriedPointSecondKey.gameDifficulty,
                        value: m.default.getInstance().getGameDifficulty(),
                      })),
                  this.gameMode == c.GameMode.Local &&
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.LocalGameOver,
                        value: this.getDurationTime(),
                      });
              }),
              (t.prototype.moveMapNode = function (e) {
                (this.playerInfoNode.active = !1),
                  (this.nodeUseProps.active = !1),
                  (this.topNode.active = !1),
                  (this.mapNode.scale = 0.7 * this.mapNode.scale),
                  (this.mapNode.x = -4.045),
                  p.default.getInstance().getTools().getSkinInfo(),
                  (this.mapNode.y = 343.613),
                  this.showWinPlayerFlag(e);
              }),
              (t.prototype.getDurationTime = function () {
                return I.default.getCurTimeStamp() - this._timestamp;
              }),
              (t.prototype.onFirstRankBackToHall = function () {
                var e = m.default.getInstance().getPlayerWinGold();
                p.default.getInstance().setWinGoldQuit(e.first),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameOverOther,
                      gameResult: c.GameResult.Success,
                      usePropCount: this._usePropsView.getUsePropsInfo(),
                      gameDifficulty: m.default
                        .getInstance()
                        .getGameDifficulty(),
                      isAdvanceQuit: !0,
                      duration: this.getDurationTime(),
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameOverOther,
                      actionName: c.BuriedPointSecondKey.gameResult,
                      value: c.GameResult.Success,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameOverOther,
                      actionName: c.BuriedPointSecondKey.gameDifficulty,
                      value: m.default.getInstance().getGameDifficulty(),
                    }),
                  f.default
                    .getInstance()
                    .changeLuck(
                      y.default
                        .getInstance()
                        .getMyselfUserInfo()
                        .getPlayerIndex(),
                      c.LuckChangeType.Win
                    ),
                  this.backToHall();
              }),
              (t.prototype.onBackToHall = function (e) {
                if (null != e) {
                  if (
                    (u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.MidwayQuit,
                        quitType: e,
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.MidwayQuit,
                        actionName: c.BuriedPointSecondKey.quitType,
                        value: e,
                      }),
                    p.default.getInstance().setExitType(e),
                    this.gameMode != c.GameMode.Local &&
                      f.default
                        .getInstance()
                        .changeLuck(
                          y.default
                            .getInstance()
                            .getMyselfUserInfo()
                            .getPlayerIndex(),
                          c.LuckChangeType.Lost
                        ),
                    e == c.MidwayQuitType.Quit)
                  )
                    if (this.gameMode == c.GameMode.Local) {
                      var t = {
                        totalGameCount: y.default
                          .getInstance()
                          .getGameTotalRounds(),
                        gameCount: p.default
                          .getInstance()
                          .getOpenAppPlayGameCount(),
                        gameDuration: this.getDurationTime(),
                      };
                      u.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: c.BuriedOneKey.localGameRoom,
                          actionName: c.BuriedTwoKey.midwayExit,
                          value: t,
                        });
                    } else
                      (t = {
                        totalGameCount: y.default
                          .getInstance()
                          .getGameTotalRounds(),
                        gameCount: p.default
                          .getInstance()
                          .getOpenAppPlayGameCount(),
                        gameDuration: this.getDurationTime(),
                        gameResult: 0,
                        playerFirstDice6Num: p.default
                          .getInstance()
                          .getFirstSixIndex(),
                        playerStepChessCount: p.default
                          .getInstance()
                          .getEatOther(),
                        playerStepedChessCount: p.default
                          .getInstance()
                          .getMyBeEatenOther(),
                        playerFirstTimeStepDura: p.default
                          .getInstance()
                          .getFirstEatChessTime(),
                        undoCount: p.default.getInstance().getUndoCount(),
                      }),
                        u.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: I.default.getEventName(),
                            actionName: c.BuriedTwoKey.midwayExit,
                            value: t,
                          });
                } else
                  p.default.getInstance().setExitType(c.MidwayQuitType.Quit);
                this.backToHall();
              }),
              (t.prototype.backToHall = function () {
                l.default.getInstance().stopAllAudio(),
                  p.default.getInstance().setIsAgain(!1),
                  this.gameMode == c.GameMode.Local &&
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.LocalGameMidwayQuit,
                        value: this.getDurationTime(),
                      });
                var e = this.gameMode;
                e == c.GameMode.Local
                  ? u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.enterGameHall,
                        actionName: c.BuriedTwoKey.fromLocalGame,
                      })
                  : e == c.GameMode.Computer
                  ? u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.enterGameHall,
                        actionName: c.BuriedTwoKey.fromRobotGame,
                      })
                  : u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.enterGameHall,
                        actionName: c.BuriedTwoKey.fromOnlineGame,
                      }),
                  y.default.getInstance().setGameSettingInfo(!0, !0),
                  cc.director.loadScene("Hall");
              }),
              (t.prototype.onClickGameQuit = function () {
                var e = this;
                u.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: I.default.getEventName(),
                    actionName: c.BuriedTwoKey.settingBtnClick,
                  });
                var t;
                (t =
                  this.gameMode == c.GameMode.Online
                    ? c.ADType.ShowOlExit
                    : this.gameMode == c.GameMode.Computer
                    ? c.ADType.ShowPcExit
                    : c.ADType.ShowLocalExit),
                  v.default.preInterstitialReady(t),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  this._isFirstRank ||
                    this.loadRes(
                      s.GAME_PREFAB_PATH + "QuitGameSettingView",
                      cc.Prefab,
                      function (t) {
                        cc.instantiate(t).parent = e.node_base;
                      }
                    );
              }),
              (t.prototype.showTestUI = function (e) {
                e && this._isshowTestUIUI
                  ? (this.nodeDiceTestUI.active = !0)
                  : (this.nodeDiceTestUI.active = !1);
              }),
              (t.prototype.hideTestUI = function () {
                this.showTestUI(!1);
              }),
              (t.prototype.onRemoveBarrier = function (e) {
                var t = this._barrierGrids[e];
                t && t.disappearBarrier();
              }),
              (t.prototype.onDestroy = function () {
                e.prototype.onDestroy.call(this),
                  h.default.getInstance().clearData(),
                  d.default.getInstance().clearData(),
                  y.default.getInstance().clearData();
                var t = y.default
                  .getInstance()
                  .getGameSettingInfo().musicStatus;
                l.default.getInstance().setMusicOpen(t),
                  p.default.getInstance().setFirstSixIndex(0),
                  (p.default.getInstance()._myBeEatenOther = 0),
                  (p.default.getInstance()._eatOther = 0),
                  (p.default.getInstance()._firstEatChessTime = 0),
                  (p.default.getInstance()._undoCount = 0);
              }),
              (t.prototype.closePlayerCD = function (e) {
                this._playerInfos[e].closeCD();
              }),
              (t.prototype.setCurrentDicePoints = function (e) {
                (this.labDicePoints.string = "\u8272\u5b50\u70b9\u6570:" + e),
                  p.default.getInstance().setDicePoints(e);
              }),
              (t.prototype.onRollTheDice = function (e, t) {
                var n = this;
                this.setCurrentDicePoints(e);
                var o = y.default.getInstance().getMyselfUserInfo();
                this._turnPlayerIndex == o.getPlayerIndex() &&
                  (d.default
                    .getInstance()
                    .disablePlayerAllChesss(this._turnPlayerIndex),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.RollDice,
                      dicePoints: e,
                      isClickDice: !t,
                      isOneToFive: e <= 5,
                    }));
                var a = d.default
                  .getInstance()
                  .getPlayerCanWalkChess(this._turnPlayerIndex, e);
                if (0 == a.length)
                  this.closePlayerCD(this._turnPlayerIndex),
                    this.node.stopAllActions(),
                    this.node.runAction(
                      cc.sequence(
                        cc.delayTime(0.3),
                        cc.callFunc(function () {
                          n.turnPlayerOperation();
                        })
                      )
                    );
                else if (1 == a.length) {
                  var i = a[0];
                  this.closePlayerCD(this._turnPlayerIndex), i.walk(e);
                } else if (this._turnPlayerIndex == o.getPlayerIndex())
                  if (null == t) {
                    for (var r = !1, s = 0; s < a.length; s++) {
                      i = a[s];
                      for (var l = s + 1; l < a.length; l++) {
                        var p = a[l];
                        if (
                          i.getCurrentPosIndex() - 1 ==
                            p.getCurrentPosIndex() ||
                          i.getCurrentPosIndex() + 1 == p.getCurrentPosIndex()
                        ) {
                          i.setNodeClickScale(!1),
                            p.setNodeClickScale(!1),
                            (r = !0);
                          break;
                        }
                      }
                      r || i.setNodeClickScale(!0),
                        m.default.getInstance().getIsOverTime() ||
                          i.setChessCanClick(!0);
                    }
                    d.default.getInstance().changeMyChessSize(a, !0);
                  } else a[I.default.getRandomNum(0, a.length - 1)].walk(e);
                else if (this.playerIsRobot(this._turnPlayerIndex))
                  g.default.getInstance().walk(a, e, this._turnPlayerIndex);
                else {
                  for (r = !1, s = 0; s < a.length; s++) {
                    for (i = a[s], l = s + 1; l < a.length; l++)
                      if (
                        ((p = a[l]),
                        i.getCurrentPosIndex() - 1 == p.getCurrentPosIndex() ||
                          i.getCurrentPosIndex() + 1 == p.getCurrentPosIndex())
                      ) {
                        i.setNodeClickScale(!1),
                          p.setNodeClickScale(!1),
                          (r = !0);
                        break;
                      }
                    r || i.setNodeClickScale(!0),
                      m.default.getInstance().getIsOverTime() ||
                        i.setChessCanClick(!0);
                  }
                  d.default.getInstance().changeMyChessSize(a, !0);
                }
              }),
              (t.prototype.onClickShop = function () {
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  p.default
                    .getInstance()
                    .getTools()
                    .popupShopView(c.ShopShowType.Gold, function () {
                      p.default.getInstance().getTools().getGlobalJson().info[0]
                        .show_game_banner && v.default.showBanner();
                    });
              }),
              (t.prototype.rollDiceAI = function (e, t) {
                (this._turnPlayerIndex = e), this.onRollTheDice(t, void 0);
              }),
              (t.prototype.showWinPlayerFlag = function () {}),
              (t.prototype.showGameDifficulty = function () {
                var e = m.default.getInstance().getGameDifficulty();
                e == c.GameDifficulty.Esay
                  ? (this.labGameDifficulty.string = "\u7b80\u5355\u6a21\u5f0f")
                  : e == c.GameDifficulty.Normal
                  ? (this.labGameDifficulty.string = "\u666e\u901a\u6a21\u5f0f")
                  : e == c.GameDifficulty.Hard &&
                    (this.labGameDifficulty.string =
                      "\u56f0\u96be\u6a21\u5f0f");
              }),
              (t.prototype.onClickSuccess = function () {
                y.default.getInstance().getAllUser(),
                  this._winUsers.push(
                    y.default.getInstance().getMyselfUserInfo()
                  ),
                  this.showGameSettlement();
              }),
              (t.prototype.onClickFail = function () {
                var e = y.default.getInstance().getAllUser();
                this._winUsers.push(e[1]), this.showGameSettlement();
              }),
              (t.prototype.onDebugNetWork = function () {
                v.default.setNetWortStatus(c.NetworkStatus.No);
              }),
              (t.prototype.onBtnOkClick = function () {
                this.turnPlayerOperation();
              }),
              (t.prototype.onBtnExpressionClick = function () {
                this._isShowExpression ||
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: I.default.getEventName(),
                      actionName: c.BuriedTwoKey.interactBtnClick,
                    }),
                  (this._isShowExpression = !this._isShowExpression);
              }),
              (t.prototype.onBtnSendExpessionClick = function (e, t) {
                var n = { playerIndex: 0, expressionName: t };
                u.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: I.default.getEventName(),
                    actionName: c.BuriedTwoKey.sendExpression,
                    value: t,
                  }),
                  cc.director.emit(c.GameEvent.send_Expression, n),
                  this.scheduleOnce(function () {
                    g.default.getInstance().randomSendExpression(!0);
                  }, 5),
                  this.onBtnExpressionClick();
              }),
              (t.prototype.onBtnSendSentenceClick = function (e, t) {
                var n = { playerIndex: 0, expressionName: t };
                u.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: I.default.getEventName(),
                    actionName: c.BuriedTwoKey.sendSentence,
                    value: t,
                  }),
                  cc.director.emit(c.GameEvent.send_Sentence, n),
                  this.scheduleOnce(function () {
                    g.default.getInstance().robotReply(t);
                  }, 3),
                  this.onBtnExpressionClick();
              }),
              (t.prototype.onBtnGuideFourClick = function () {
                (this.classice_guide.active = !1),
                  cc.director.emit(c.GameEvent.Guide_Select_Chess, {
                    playerIndex: 0,
                    chessIndes: 3,
                  });
              }),
              (t.prototype.onBtnGuideSixClick = function () {
                (this.quick_guide.active = !1),
                  cc.director.emit(c.GameEvent.Guide_Select_Chess, {
                    playerIndex: 0,
                    chessIndes: 1,
                  });
              }),
              (t.prototype.showGuide = function () {
                this.gameMode != c.GameMode.Local &&
                this.gameMode != c.GameMode.BombItem &&
                this.gameMode != c.GameMode.Roadblock
                  ? ((this.chessNode.zIndex = 0),
                    (this.playerInfoNode.zIndex = 0),
                    (this.guide_node.zIndex = 1),
                    (m.default.getInstance().getComputerRoomMode() !=
                      c.GameRoomMode.Classic &&
                      m.default.getInstance().getRoomMode() !=
                        c.GameRoomMode.Classic) ||
                    this.gameMode == c.GameMode.Local
                      ? (this.quick_guide.active = !0)
                      : (this.classice_guide.active = !0))
                  : (this.chessNode.zIndex = 1);
              }),
              (t.prototype.showSafeGuide = function (e) {
                this.gameMode != c.GameMode.Local &&
                this.gameMode != c.GameMode.BombItem &&
                this.gameMode != c.GameMode.Roadblock
                  ? ((this.chessNode.zIndex = 0),
                    (this.playerInfoNode.zIndex = 0),
                    (this.guide_node.zIndex = 1),
                    (this.safe_Node.active = !0),
                    (this._guideParam = e))
                  : cc.director.emit(
                      c.GameEvent.Player_Operation_Completed,
                      this._guideParam.ownerPlayerIndex,
                      this._guideParam.isEatOther,
                      this._guideParam._isArriveTerminalPoint
                    );
              }),
              (t.prototype.closeGuide = function () {
                (this.classice_guide.active = !1),
                  (this.quick_guide.active = !1),
                  (this.safe_Node.active = !1);
              }),
              (t.prototype.onBtnGuideOkClick = function () {
                (this.safe_Node.active = !1),
                  cc.director.emit(
                    c.GameEvent.Player_Operation_Completed,
                    this._guideParam.ownerPlayerIndex,
                    this._guideParam.isEatOther,
                    this._guideParam._isArriveTerminalPoint
                  );
              }),
              (t.prototype.onBtnShowUndoClick = function () {
                (this.node_undo.active = !this.node_undo.active),
                  0 == this.node_undo.active
                    ? p.default.getInstance().setUndoIndex(0)
                    : this.getUndoIndex(),
                  p.default.getInstance().getIsCompleteUndoPower()
                    ? (this.undo_guide.active = !1)
                    : (this.undo_guide.active = !0);
              }),
              (t.prototype.onBtnSelectUndoClick = function (e, t) {
                if (parseInt(t) != this._undoIndex) {
                  p.default.getInstance().setUndoIndex(parseInt(t)),
                    (this.node_undo.active = !1);
                  for (var n = 0; n < 4; n++) {
                    var o = this.undo_list[n].getChildByName("img_select");
                    parseInt(t) - 1 == n ? (o.active = !0) : (o.active = !1);
                  }
                } else p.default.getInstance().setUndoIndex(0);
              }),
              (t.prototype.getUndoIndex = function () {
                for (
                  var e = y.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .getPlayerIndex(),
                    t = d.default.getInstance().getPlayerAllChess(e),
                    n = [],
                    o = [],
                    a = 6;
                  a >= 1;
                  a--
                )
                  if (
                    (o = g.default.getInstance().getCanEateOtherChess(t, a))
                      .length > 0
                  ) {
                    var i = { diceCount: 0, chessLength: 0 };
                    (i.diceCount = a), (i.chessLength = o.length), n.push(i);
                  }
                if (n.length > 0)
                  switch (
                    (n.sort(function (e, t) {
                      return e.chessLength - t.chessLength;
                    }),
                    n[0].diceCount)
                  ) {
                    case 6:
                      this.undo_list[0].getComponent(cc.Animation).play(),
                        this.undo_list[3].getComponent(cc.Animation).play();
                      break;
                    case 5:
                      this.undo_list[0].getComponent(cc.Animation).play(),
                        this.undo_list[2].getComponent(cc.Animation).play();
                      break;
                    case 4:
                      this.undo_list[0].getComponent(cc.Animation).play(),
                        this.undo_list[3].getComponent(cc.Animation).play();
                      break;
                    case 3:
                      this.undo_list[1].getComponent(cc.Animation).play(),
                        this.undo_list[2].getComponent(cc.Animation).play();
                      break;
                    case 2:
                      this.undo_list[1].getComponent(cc.Animation).play(),
                        this.undo_list[3].getComponent(cc.Animation).play();
                      break;
                    case 1:
                      this.undo_list[1].getComponent(cc.Animation).play(),
                        this.undo_list[2].getComponent(cc.Animation).play();
                  }
              }),
              (t.prototype.showUndoHelp = function () {
                var e = this;
                this.gameMode != c.GameMode.Local &&
                  this.loadRes(
                    s.GAME_PREFAB_PATH + "UndoHelp",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node;
                    }
                  );
              }),
              (t.prototype.showUndoDice = function () {}),
              (t.prototype.onBtnOKCloseClick = function () {
                (this.quickGuide.active = !1), (this.classiceGuide.active = !1);
              }),
              (t.prototype.onShowQuitPrizeView = function () {
                var e = this;
                this.gameMode == c.GameMode.Online
                  ? this.loadRes(
                      s.GAME_PREFAB_PATH + "QuitPrizeView",
                      cc.Prefab,
                      function (t) {
                        var n = cc.instantiate(t);
                        n.parent = e.node;
                        var o = n.getComponent(S.default),
                          a = m.default.getInstance().getPlayerWinGold();
                        (e.node_base.active = !1),
                          o.setInfo(a.first, function () {
                            e.node_base.active = !0;
                          });
                      }
                    )
                  : this.backToHall();
              }),
              (t.prototype.onBtnAddPlayerClick = function () {
                var e = this;
                this.loadRes(
                  s.GAME_PREFAB_PATH + "Add_Player",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node;
                  }
                ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.localGameRoom,
                      actionName: c.BuriedTwoKey.modifyBtnClick,
                    });
              }),
              i([R(cc.Label)], t.prototype, "labTurnPlayerIndex", void 0),
              i([R(cc.Label)], t.prototype, "labDicePoints", void 0),
              i([R(cc.Node)], t.prototype, "mapGridNode", void 0),
              i([R(cc.Node)], t.prototype, "chessNode", void 0),
              i([R(cc.Node)], t.prototype, "mapNode", void 0),
              i([R(cc.Node)], t.prototype, "playerInfoNode", void 0),
              i([R(cc.Node)], t.prototype, "topNode", void 0),
              i([R(cc.Sprite)], t.prototype, "sprChessBaseBgs", void 0),
              i([R(cc.Node)], t.prototype, "playerInfoNodes", void 0),
              i([R(cc.Node)], t.prototype, "terminalAnimNodes", void 0),
              i([R(cc.SpriteFrame)], t.prototype, "spfGameModes", void 0),
              i([R(cc.Node)], t.prototype, "nodeUseProps", void 0),
              i([R(cc.Prefab)], t.prototype, "usePropsViewPrefab", void 0),
              i([R(cc.Prefab)], t.prototype, "mapGridPrefab", void 0),
              i([R(cc.Prefab)], t.prototype, "chessPrefab", void 0),
              i([R(cc.Prefab)], t.prototype, "playerInfoPrefab", void 0),
              i([R(cc.Sprite)], t.prototype, "sprCenter", void 0),
              i([R(cc.Node)], t.prototype, "mainNode", void 0),
              i([R(Number)], t.prototype, "mainNodeScale", void 0),
              i([R(cc.Label)], t.prototype, "labGameDifficulty", void 0),
              i([R(cc.Node)], t.prototype, "nodeDiceTestUI", void 0),
              i([R(cc.Sprite)], t.prototype, "node_terminal", void 0),
              i([R(cc.Sprite)], t.prototype, "img_center", void 0),
              i([R(cc.Node)], t.prototype, "node_base", void 0),
              i([R(cc.Node)], t.prototype, "classice_guide", void 0),
              i([R(cc.Node)], t.prototype, "quick_guide", void 0),
              i([R(cc.Node)], t.prototype, "safe_Node", void 0),
              i([R(cc.Node)], t.prototype, "guide_node", void 0),
              i([R(cc.Node)], t.prototype, "node_undo", void 0),
              i([R(cc.Node)], t.prototype, "undo_list", void 0),
              i([R(cc.Node)], t.prototype, "undo_guide", void 0),
              i([R(cc.Node)], t.prototype, "quickGuide", void 0),
              i([R(cc.Node)], t.prototype, "classiceGuide", void 0),
              i([R(cc.Node)], t.prototype, "node_bian", void 0),
              i([R(cc.Node)], t.prototype, "node_player", void 0),
              i([M], t)
            );
          })(r.default);
        (n.default = G), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/ChessManager": "ChessManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/LuckManager": "LuckManager",
        "../Framework/Manager/MapGridManager": "MapGridManager",
        "../Framework/Manager/RobotManager": "RobotManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/ShopDataManager": "ShopDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "./Chess": "Chess",
        "./GameSettlementView": "GameSettlementView",
        "./MapGrid": "MapGrid",
        "./PlayerInfo": "PlayerInfo",
        "./QuitPrizeView": "QuitPrizeView",
        "./UsePropsView": "UsePropsView",
      },
    ],
    GameSettingView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "d2879sLRb1ETrLZc4IB5ZCy", "GameSettingView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/UserInfoManager"),
          u = e("../Framework/Utils/Utils"),
          d = cc._decorator,
          p = d.ccclass,
          f = d.property,
          h = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprMusicStatus = []),
                (t.sprAudioStatus = []),
                (t.no_select_list = []),
                (t.select_list = []),
                (t.label_language_txt = null),
                (t.node_language = null),
                (t.labelOutLineList = []),
                (t.sprFrame = []),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                u.default.localStr(this.node),
                  this.registerAllEvents(),
                  this.refreshButtonStatus(),
                  this.updateLanguage();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  s.GameEvent.Select_Language,
                  this.setLanguage,
                  this
                );
              }),
              (t.prototype.setLanguage = function () {
                u.default.localStr(this.node), this.updateLanguage();
              }),
              (t.prototype.refreshButtonStatus = function () {
                var e = l.default.getInstance().getGameSettingInfo();
                (this.sprMusicStatus[0].active = e.musicStatus),
                  (this.sprMusicStatus[1].active = !e.musicStatus),
                  (this.sprAudioStatus[0].active = e.effectStatus),
                  (this.sprAudioStatus[1].active = !e.effectStatus);
              }),
              (t.prototype.updateLanguage = function () {
                var e = l.default.getInstance().getLanguage();
                this.label_language_txt.string = [
                  "English",
                  "\u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629 ",
                  "\u0939\u093f\u0928\u094d\u0926\u0940 ",
                  "\u0627\u0631\u062f\u0648 ",
                ][e - 1];
              }),
              (t.prototype.onClickMusic = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = l.default
                  .getInstance()
                  .getGameSettingInfo().musicStatus;
                l.default.getInstance().setGameSettingInfo(!e, null),
                  c.default.getInstance().setMusicOpen(!e),
                  this.refreshButtonStatus();
              }),
              (t.prototype.onClickAudio = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = l.default
                  .getInstance()
                  .getGameSettingInfo().effectStatus;
                l.default.getInstance().setGameSettingInfo(null, !e),
                  c.default.getInstance().setEffectOpen(!e),
                  this.refreshButtonStatus();
              }),
              (t.prototype.onBtnGuideClick = function () {
                cc.director.loadScene("Game_guide");
              }),
              (t.prototype.onBtnLanguageClick = function (e, t) {
                var n = parseInt(t);
                l.default.getInstance().setLanguage(n),
                  cc.director.emit(s.GameEvent.Select_Language),
                  (this.node_language.active = !1);
              }),
              (t.prototype.onBtnEnglishClick = function () {
                this.node_language.active = !0;
                for (
                  var e = l.default.getInstance().getLanguage(), t = 0;
                  t < this.no_select_list.length;
                  t++
                )
                  t == e - 1
                    ? ((this.no_select_list[t].active = !1),
                      (this.select_list[t].active = !0),
                      (this.labelOutLineList[t].color = cc.color(145, 78, 0)))
                    : ((this.no_select_list[t].active = !0),
                      (this.select_list[t].active = !1),
                      (this.labelOutLineList[t].color = cc.color(0, 106, 169)));
              }),
              (t.prototype.onCloseClick = function () {
                cc.director.emit(s.GameEvent.Close_Parent_Ui), this.onClose();
              }),
              (t.prototype.onBtnPRclick = function () {
                cc.sys.openURL(
                  "https://www.volcanoh5game.com/LudoLive-PrivacyPolicy/"
                );
              }),
              i([f(cc.Node)], t.prototype, "sprMusicStatus", void 0),
              i([f(cc.Node)], t.prototype, "sprAudioStatus", void 0),
              i([f(cc.Node)], t.prototype, "no_select_list", void 0),
              i([f(cc.Node)], t.prototype, "select_list", void 0),
              i([f(cc.Label)], t.prototype, "label_language_txt", void 0),
              i([f(cc.Node)], t.prototype, "node_language", void 0),
              i([f(cc.LabelOutline)], t.prototype, "labelOutLineList", void 0),
              i([f(cc.SpriteFrame)], t.prototype, "sprFrame", void 0),
              i([p], t)
            );
          })(r.default);
        (n.default = h), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    GameSettlementView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "356a30Vg/9NL6Z2o4QpZvKt", "GameSettlementView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Utils/Utils"),
          p = e("../Framework/Manager/TaskManager"),
          f = e("../Framework/Manager/GameDataManager"),
          h = e("../Framework/Manager/RoomInfoManager"),
          g = e("../Framework/Manager/BuriedPointManager"),
          m = e("../Hall/OnlineRewardView"),
          _ = e("../Framework/Native/NativeBridge"),
          y = e("../Framework/Manager/CirculateManager"),
          v = e("../Hall/activity/bombResult"),
          I = cc._decorator,
          C = I.ccclass,
          k = I.property,
          w = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.nodeSettlementItmes = []),
                (t.sprResultBg = null),
                (t.spfResultBgs = []),
                (t.sprResult = null),
                (t.spfResults = []),
                (t.moveAnim = null),
                (t.bgAnim = null),
                (t.huangguangAnim = null),
                (t.nodeSettlement = null),
                (t.nodeSuccess = null),
                (t.nodeFail = null),
                (t.nodeBG = null),
                (t.sprHuangguan = null),
                (t.itembgList = []),
                (t.sprFrame = []),
                (t.node_again = null),
                (t.node_btnRevise = null),
                (t._perAddValue = 0),
                (t._progressValue = 0),
                (t._winPlayerIndex = 0),
                (t.isMyWin = !1),
                (t.gameMode = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                d.default.localStr(this.node),
                  (this.nodeBG.active = !1),
                  (this.nodeSettlement.active = !1),
                  _.default.addAHAActivityCount(),
                  (this.gameMode = h.default.getInstance().getGameMode()),
                  (this.gameMode != c.GameMode.BombItem &&
                    this.gameMode != c.GameMode.Roadblock) ||
                    this.scheduleOnce(this.onBtnbgClick, 5);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showExp = function () {
                var e = this,
                  t = u.default.getInstance().getMyselfUserInfo();
                (this._progressValue = t.getExp() / t.getLevelUpExp()),
                  (this._perAddValue = this._progressValue / 50),
                  s.ISAPPLET &&
                    !f.default.getInstance().getIsCompleteGuide() &&
                    f.default.getInstance().showAppTip &&
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "addGuideView",
                      cc.Prefab,
                      function (t) {
                        (cc.instantiate(t).parent = e.node),
                          (f.default.getInstance().showAppTip = !1);
                      }
                    );
              }),
              (t.prototype.onBtnbgClick = function () {
                var e = this;
                2 == y.default.getInstance().lostCount
                  ? this.loadRes(
                      s.HALL_PREFAB_PATH + "activity/bombResult",
                      cc.Prefab,
                      function (t) {
                        var n = cc.instantiate(t);
                        (n.parent = e.node),
                          n.getComponent(v.default).initData(!1);
                      }
                    )
                  : y.default.getInstance().isGameover
                  ? this.loadRes(
                      s.HALL_PREFAB_PATH + "activity/bombResult",
                      cc.Prefab,
                      function (t) {
                        var n = cc.instantiate(t);
                        (n.parent = e.node),
                          n.getComponent(v.default).initData(!0);
                      }
                    )
                  : cc.director.loadScene("Hall");
              }),
              (t.prototype.setInfo = function (e, t, n) {
                var o = this;
                this._winPlayerIndex = n[0].userInfo.getPlayerIndex();
                for (
                  var a = 0,
                    i = 0,
                    r = function (e) {
                      var t = n[e];
                      if (t) {
                        var o =
                            g.nodeSettlementItmes[e].getChildByName("img_bg"),
                          r =
                            g.nodeSettlementItmes[e].getChildByName(
                              "img_head_photo_bg"
                            ),
                          l = r.getChildByName("img_head_photo"),
                          d =
                            g.nodeSettlementItmes[e].getChildByName(
                              "lab_nickname"
                            ),
                          p =
                            g.nodeSettlementItmes[e].getChildByName(
                              "lab_add_coins"
                            );
                        g.loadRes(
                          s.PLAYER_HEAD_PHOTO_PATH +
                            "img_head_photo_" +
                            t.userInfo.getHeadPhotoIdx(),
                          cc.SpriteFrame,
                          function (e) {
                            l.getComponent(cc.Sprite).spriteFrame = e;
                          }
                        ),
                          (g.gameMode != c.GameMode.BombItem &&
                            g.gameMode != c.GameMode.Roadblock) ||
                            ((p.active = !1),
                            t.userInfo.getUserId() ==
                              u.default
                                .getInstance()
                                .getMyselfUserInfo()
                                .getUserId() && (i = e + 1)),
                          t.isWin
                            ? ((a = e),
                              (r.getComponent(cc.Sprite).spriteFrame =
                                g.sprFrame[0]))
                            : (r.getComponent(cc.Sprite).spriteFrame =
                                g.sprFrame[1]),
                          (d.getComponent(cc.Label).string =
                            t.userInfo.getNickName()),
                          (p.getComponent(cc.Label).string = t.isWin
                            ? "+" + t.winGold
                            : "Lost"),
                          (o.getComponent(cc.Sprite).spriteFrame = t.isWin
                            ? g.itembgList[0]
                            : g.itembgList[1]);
                      } else g.nodeSettlementItmes[e].active = !1;
                    },
                    g = this,
                    m = 0;
                  m < this.nodeSettlementItmes.length;
                  m++
                )
                  r(m);
                (this.isMyWin = e),
                  this.gameMode == c.GameMode.Local
                    ? ((this.sprResultBg.spriteFrame = this.spfResultBgs[0]),
                      (this.sprResult.spriteFrame = this.spfResults[2]),
                      (this.nodeBG.active = !0),
                      (this.nodeSettlement.active = !0),
                      this.moveAnim.play("settlement_anim"),
                      this.huangguangAnim.play("huangguan"))
                    : h.default.getInstance().getGameMode() ==
                        c.GameMode.BombItem ||
                      h.default.getInstance().getGameMode() ==
                        c.GameMode.Roadblock
                    ? ((this.nodeBG.active = !0),
                      (this.nodeSettlement.active = !0),
                      (this.node_again.active = !1),
                      (this.node_btnRevise.active = !1),
                      this.isMyWin
                        ? (y.default.getInstance().competitionList.push(1),
                          (this.sprResultBg.spriteFrame = this.spfResultBgs[0]),
                          (this.sprResult.spriteFrame = this.spfResults[0]))
                        : (y.default.getInstance().lostCount++,
                          y.default.getInstance().competitionList.push(0),
                          (this.sprResultBg.spriteFrame = this.spfResultBgs[1]),
                          (this.sprResult.spriteFrame = this.spfResults[1])),
                      y.default.getInstance().competitionCount++,
                      y.default.getInstance().setRankIndex(this.isMyWin, i))
                    : (e
                        ? (l.default
                            .getInstance()
                            .playEffectWithPath(c.AudioType.Settlement_Win),
                          (this.sprResultBg.spriteFrame = this.spfResultBgs[0]),
                          (this.sprResult.spriteFrame = this.spfResults[0]),
                          (this.sprResult.node.y = 357),
                          (f.default.getInstance().isWin = !0))
                        : (l.default
                            .getInstance()
                            .playEffectWithPath(c.AudioType.Settlement_Lose),
                          (this.sprResultBg.spriteFrame = this.spfResultBgs[1]),
                          (this.sprResult.spriteFrame = this.spfResults[1]),
                          (this.huangguangAnim.node.active = !1),
                          (this.sprResult.node.y = 447)),
                      p.default
                        .getInstance()
                        .setTaskProgress(c.TaskType.Task_complete),
                      u.default.getInstance().getMyselfUserInfo(),
                      this.node.runAction(
                        cc.sequence(
                          cc.delayTime(0.1),
                          cc.callFunc(function () {
                            cc.director.emit(
                              c.GameEvent.Move_Map_Node,
                              n[0].userInfo.getPlayerIndex()
                            ),
                              (o.nodeBG.active = !0),
                              (o.nodeSettlement.active = !0),
                              e ||
                                ((o.sprHuangguan.active = !0),
                                (o.sprHuangguan.y = 279 - 124 * a)),
                              o.moveAnim.play("settlement_anim"),
                              o.huangguangAnim.play("huangguan"),
                              e
                                ? d.default.regAnimationFinishEvent(
                                    o.huangguangAnim,
                                    function () {
                                      o.showExp();
                                    }
                                  )
                                : d.default.regAnimationFinishEvent(
                                    o.moveAnim,
                                    function () {
                                      o.showExp();
                                    }
                                  );
                          })
                        )
                      ));
              }),
              (t.prototype.onClickBackToHall = function () {
                var e;
                (e =
                  this.gameMode == c.GameMode.Online
                    ? c.ADType.ShowOlExit
                    : this.gameMode == c.GameMode.Computer
                    ? c.ADType.ShowPcExit
                    : c.ADType.ShowLocalExit),
                  _.default.watchVideo(function () {
                    g.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: d.default.getEventName(),
                        actionName: c.BuriedTwoKey.backBtnClick,
                      }),
                      l.default
                        .getInstance()
                        .playEffectWithPath(c.AudioType.Button_Click),
                      f.default.getInstance().setIsAgain(!1),
                      cc.director.emit(c.GameEvent.Bakc_To_Hall);
                  }, e);
              }),
              (t.prototype.onBtnAgainClick = function () {
                var e = this;
                g.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: d.default.getEventName(),
                    actionName: c.BuriedTwoKey.againBtnClick,
                  });
                var t = u.default.getInstance().getMyselfUserInfo();
                u.default.getInstance().getGoldCount() < 3 &&
                t.getGoldNum() < 1e3
                  ? f.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        d.default.replaceStr("store_insufficientgoldcoins")
                      )
                  : (this.loadRes(
                      s.HALL_PREFAB_PATH + "CoinsNotEnoughView",
                      cc.Prefab,
                      function (t) {
                        cc.instantiate(t).parent = e.node;
                      }
                    ),
                    l.default
                      .getInstance()
                      .playEffectWithPath(c.AudioType.Button_Click));
              }),
              (t.prototype.onBtnReviseClick = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  l.default.getInstance().stopAllAudio();
                var t,
                  n = f.default.getInstance().getTools().getGlobalJson()
                    .info[0].show_back_hall_insert;
                if (
                  ((t =
                    this.gameMode == c.GameMode.Online
                      ? c.ADType.ShowOlExit
                      : this.gameMode == c.GameMode.Computer
                      ? c.ADType.ShowPcExit
                      : c.ADType.ShowLocalExit),
                  n)
                )
                  _.default.watchVideo(function () {
                    var t = u.default.getInstance().getOnlineTime();
                    t > 900 && t <= 1800
                      ? e.loadRes(
                          s.HALL_PREFAB_PATH + "OnlineRewardView",
                          cc.Prefab,
                          function (t) {
                            var n = cc.instantiate(t);
                            (n.parent = e.node),
                              n
                                .getComponent(m.default)
                                .setCallBack(function () {
                                  f.default.getInstance().setOpenRoom(!0),
                                    g.default
                                      .getInstance()
                                      .sendBuriedPointInfo({
                                        event: d.default.getEventName(),
                                        actionName:
                                          c.BuriedTwoKey.reviseBtnClick,
                                      }),
                                    cc.director.loadScene("Hall");
                                });
                          }
                        )
                      : (f.default.getInstance().setOpenRoom(!0),
                        g.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: d.default.getEventName(),
                            actionName: c.BuriedTwoKey.reviseBtnClick,
                          }),
                        cc.director.loadScene("Hall"));
                  }, t);
                else {
                  var o = u.default.getInstance().getOnlineTime();
                  o > 900 && o <= 1800
                    ? this.loadRes(
                        s.HALL_PREFAB_PATH + "OnlineRewardView",
                        cc.Prefab,
                        function (t) {
                          var n = cc.instantiate(t);
                          (n.parent = e.node),
                            n.getComponent(m.default).setCallBack(function () {
                              f.default.getInstance().setOpenRoom(!0),
                                g.default
                                  .getInstance()
                                  .sendBuriedPointInfo({
                                    event: d.default.getEventName(),
                                    actionName: c.BuriedTwoKey.reviseBtnClick,
                                  }),
                                cc.director.loadScene("Hall");
                            });
                        }
                      )
                    : (f.default.getInstance().setOpenRoom(!0),
                      g.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: d.default.getEventName(),
                          actionName: c.BuriedTwoKey.reviseBtnClick,
                        }),
                      cc.director.loadScene("Hall"));
                }
              }),
              (t.prototype.onBtnPlayClick = function () {
                var e,
                  t = this;
                if (
                  ((e =
                    this.gameMode == c.GameMode.Online
                      ? c.ADType.ShowOlExit
                      : this.gameMode == c.GameMode.Computer
                      ? c.ADType.ShowPcExit
                      : c.ADType.ShowLocalExit),
                  f.default.getInstance().getTools().getGlobalJson().info[0]
                    .show_back_hall_insert)
                )
                  _.default.watchVideo(function () {
                    var e = u.default.getInstance().getOnlineTime();
                    if (e > 900 && e <= 1800)
                      t.loadRes(
                        s.HALL_PREFAB_PATH + "OnlineRewardView",
                        cc.Prefab,
                        function (e) {
                          var n = cc.instantiate(e);
                          (n.parent = t.node),
                            n.getComponent(m.default).setCallBack(function () {
                              var e = h.default.getInstance().getEntryGold();
                              u.default
                                .getInstance()
                                .getMyselfUserInfo()
                                .getGoldNum() >= e
                                ? (f.default.getInstance().setIsAgain(!0),
                                  cc.director.loadScene("Hall"))
                                : (t.loadRes(
                                    s.HALL_PREFAB_PATH + "CoinsNotEnoughView",
                                    cc.Prefab,
                                    function (e) {
                                      cc.instantiate(e).parent = t.node;
                                    }
                                  ),
                                  f.default.getInstance().setIsAgain(!1));
                            });
                        }
                      );
                    else {
                      var n = h.default.getInstance().getEntryGold();
                      u.default
                        .getInstance()
                        .getMyselfUserInfo()
                        .getGoldNum() >= n
                        ? (f.default.getInstance().setIsAgain(!0),
                          cc.director.loadScene("Hall"))
                        : (t.loadRes(
                            s.HALL_PREFAB_PATH + "CoinsNotEnoughView",
                            cc.Prefab,
                            function (e) {
                              cc.instantiate(e).parent = t.node;
                            }
                          ),
                          f.default.getInstance().setIsAgain(!1));
                    }
                  }, e);
                else {
                  var n = u.default.getInstance().getOnlineTime();
                  if (n > 900 && n <= 1800)
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "OnlineRewardView",
                      cc.Prefab,
                      function (e) {
                        var n = cc.instantiate(e);
                        (n.parent = t.node),
                          n.getComponent(m.default).setCallBack(function () {
                            var e = h.default.getInstance().getEntryGold();
                            u.default
                              .getInstance()
                              .getMyselfUserInfo()
                              .getGoldNum() >= e
                              ? (f.default.getInstance().setIsAgain(!0),
                                cc.director.loadScene("Hall"))
                              : (t.loadRes(
                                  s.HALL_PREFAB_PATH + "CoinsNotEnoughView",
                                  cc.Prefab,
                                  function (e) {
                                    cc.instantiate(e).parent = t.node;
                                  }
                                ),
                                f.default.getInstance().setIsAgain(!1));
                          });
                      }
                    );
                  else {
                    var o = h.default.getInstance().getEntryGold();
                    u.default.getInstance().getMyselfUserInfo().getGoldNum() >=
                    o
                      ? (f.default.getInstance().setIsAgain(!0),
                        cc.director.loadScene("Hall"))
                      : (this.loadRes(
                          s.HALL_PREFAB_PATH + "CoinsNotEnoughView",
                          cc.Prefab,
                          function (e) {
                            cc.instantiate(e).parent = t.node;
                          }
                        ),
                        f.default.getInstance().setIsAgain(!1));
                  }
                }
              }),
              (t.prototype.onBtnActivityClick = function () {
                _.default.openAHA();
              }),
              i([k(cc.Node)], t.prototype, "nodeSettlementItmes", void 0),
              i([k(cc.Sprite)], t.prototype, "sprResultBg", void 0),
              i([k(cc.SpriteFrame)], t.prototype, "spfResultBgs", void 0),
              i([k(cc.Sprite)], t.prototype, "sprResult", void 0),
              i([k(cc.SpriteFrame)], t.prototype, "spfResults", void 0),
              i([k(cc.Animation)], t.prototype, "moveAnim", void 0),
              i([k(cc.Animation)], t.prototype, "bgAnim", void 0),
              i([k(cc.Animation)], t.prototype, "huangguangAnim", void 0),
              i([k(cc.Node)], t.prototype, "nodeSettlement", void 0),
              i([k(cc.Node)], t.prototype, "nodeSuccess", void 0),
              i([k(cc.Node)], t.prototype, "nodeFail", void 0),
              i([k(cc.Node)], t.prototype, "nodeBG", void 0),
              i([k(cc.Node)], t.prototype, "sprHuangguan", void 0),
              i([k(cc.SpriteFrame)], t.prototype, "itembgList", void 0),
              i([k(cc.SpriteFrame)], t.prototype, "sprFrame", void 0),
              i([k(cc.Node)], t.prototype, "node_again", void 0),
              i([k(cc.Node)], t.prototype, "node_btnRevise", void 0),
              i([C], t)
            );
          })(r.default);
        (n.default = w), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/CirculateManager": "CirculateManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/TaskManager": "TaskManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "../Hall/OnlineRewardView": "OnlineRewardView",
        "../Hall/activity/bombResult": "bombResult",
      },
    ],
    GetRewardView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "08356VBrGdNqZnXIZ17DWk+", "GetRewardView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameConst"),
          c = e("../../Framework/Enum/GameEnum"),
          l = e("../../Framework/Manager/AudioManager"),
          u = e("../../Framework/Manager/BuriedPointManager"),
          d = e("../../Framework/Manager/GameDataManager"),
          p = e("../../Framework/Manager/GlobalTimerManager"),
          f = e("../../Framework/Manager/UserInfoManager"),
          h = e("../../Framework/Native/NativeBridge"),
          g = e("../../Framework/Utils/Utils"),
          m = cc._decorator,
          _ = m.ccclass,
          y = m.property,
          v = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labRewardCoins = null),
                (t.labLeftSpinCount = null),
                (t.labCD = null),
                (t.btnSpinAgain = null),
                (t.sprCircleLight = null),
                (t.btn_close = null),
                (t._rewardCoins = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                var e = this;
                g.default.localStr(this.node),
                  this.registerAllEvents(),
                  this.startCDTimer(),
                  this.scheduleOnce(function () {
                    e.btn_close.node.active = !0;
                  }, 3),
                  h.default.preloadReward(c.ADType.TurntableSpinAgain);
              }),
              (t.prototype.setInfo = function (e) {
                (this._rewardCoins = e),
                  (this.labRewardCoins.string = e.toString()),
                  this.sprCircleLight.runAction(
                    cc.repeatForever(cc.rotateBy(3, 360))
                  );
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Turntable_CD_Refresh,
                  this.onRefreshCD,
                  this
                );
              }),
              (t.prototype.startCDTimer = function () {
                var e = f.default.getInstance().getTurntableInfo();
                0 == e.leftSpinCount
                  ? (this.btnSpinAgain.active = !1)
                  : ((this.btnSpinAgain.active = !0),
                    (this.labLeftSpinCount.string =
                      e.leftSpinCount.toString()));
                var t = g.default.getCurTimeStamp();
                f.default.getInstance().setTurntableInfo(t, null, e.adbonus),
                  p.default
                    .getInstance()
                    .startTurntableTimer(s.TURNTABLE_CD_TIME),
                  this.onRefreshCD(s.TURNTABLE_CD_TIME);
              }),
              (t.prototype.onRefreshCD = function (e) {
                e <= 0
                  ? (this.labCD.node.parent.active = !1)
                  : ((this.labCD.node.parent.active = !0),
                    (this.labCD.string = g.default.replaceStr(
                      "wheel_nextspin",
                      g.default.formatTime(e)
                    )));
              }),
              (t.prototype.onClickClose = function () {
                var e = this;
                this.node.parent.destroy();
                var t = d.default.getInstance().getHallGoldPos();
                this._rewardCoins &&
                  d.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(
                      c.FlyEffectType.Coins,
                      t,
                      this._rewardCoins,
                      function () {
                        var t = f.default.getInstance().getMyselfUserInfo();
                        t.setGoldNum(t.getGoldNum() + e._rewardCoins);
                      }
                    ),
                  h.default.closeBanner();
              }),
              (t.prototype.onClickSpinAgain = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click);
                var t = d.default.getInstance().getHallGoldPos();
                this._rewardCoins &&
                  d.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(
                      c.FlyEffectType.Coins,
                      t,
                      this._rewardCoins,
                      function () {
                        var t = f.default.getInstance().getMyselfUserInfo();
                        t.setGoldNum(t.getGoldNum() + e._rewardCoins),
                          (e._rewardCoins = 0);
                      }
                    ),
                  h.default.watchVideo(function () {
                    f.default.getInstance().addWatchADCount(),
                      p.default.getInstance().closeTurntableTimer();
                    var t = f.default.getInstance().getTurntableInfo();
                    f.default
                      .getInstance()
                      .setTurntableInfo(
                        0,
                        t.leftSpinCount - 1,
                        t.adbonus - 1,
                        !0
                      ),
                      d.default.getInstance().setIsAd(!0),
                      cc.director.emit(c.GameEvent.Turntable_Spin_Again),
                      e.onClose();
                  }, c.ADType.TurntableSpinAgain),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.TurntableSpinAgain,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.TurntableSpinAgain,
                    });
              }),
              (t.prototype.onClickGuessSize = function () {
                var e = this;
                this.node.parent.destroy();
                var t = d.default.getInstance().getHallGoldPos();
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  d.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(
                      c.FlyEffectType.Coins,
                      t,
                      this._rewardCoins,
                      function () {
                        var t = f.default.getInstance().getMyselfUserInfo();
                        t.setGoldNum(t.getGoldNum() + e._rewardCoins),
                          cc.director.emit(c.GameEvent.Show_Guess_Size_UI);
                      }
                    );
              }),
              i([y(cc.Label)], t.prototype, "labRewardCoins", void 0),
              i([y(cc.Label)], t.prototype, "labLeftSpinCount", void 0),
              i([y(cc.Label)], t.prototype, "labCD", void 0),
              i([y(cc.Node)], t.prototype, "btnSpinAgain", void 0),
              i([y(cc.Node)], t.prototype, "sprCircleLight", void 0),
              i([y(cc.Button)], t.prototype, "btn_close", void 0),
              i([_], t)
            );
          })(r.default);
        (n.default = v), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameConst": "GameConst",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/AudioManager": "AudioManager",
        "../../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/GlobalTimerManager": "GlobalTimerManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../../Framework/Native/NativeBridge": "NativeBridge",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    GlobalTimerManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "689b0dB7eBP/plHq/ApBBkE", "GlobalTimerManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("./GameDataManager"),
          r = e("./UserInfoManager"),
          s = (function () {
            function e() {
              (this._timingBoxCoinsSecond = 0),
                (this._timingBoxDiamondsSecond = 0),
                (this._turntableSecond = 0),
                (this._onlineSecond = 0),
                (this._adRewardSecond = 0);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.checkTimerExist = function () {}),
              (e.prototype.startTimingBoxCoinsTimer = function (e) {
                this.closeTimingBoxCoinsTimer(),
                  (this._timingBoxCoinsSecond = e);
                var t = cc.director.getScheduler();
                t.enableForTarget(this),
                  t.schedule(this.timingBoxCoinsTimer, this, 1);
              }),
              (e.prototype.timingBoxCoinsTimer = function () {
                (this._timingBoxCoinsSecond -= 1),
                  this._timingBoxCoinsSecond <= 0
                    ? (this.closeTimingBoxCoinsTimer(),
                      r.default
                        .getInstance()
                        .setTimingBoxInfo(0, 0, null, null, null, null, null),
                      cc.director.emit(
                        a.GameEvent.TimingBox_Coins_AD_Refresh,
                        this._timingBoxCoinsSecond
                      ))
                    : cc.director.emit(
                        a.GameEvent.TimingBox_Coins_AD_Refresh,
                        this._timingBoxCoinsSecond
                      );
              }),
              (e.prototype.closeTimingBoxCoinsTimer = function () {
                cc.director
                  .getScheduler()
                  .unschedule(this.timingBoxCoinsTimer, this),
                  (this._timingBoxCoinsSecond = 0);
              }),
              (e.prototype.startTimingBoxDiamondsTimer = function (e) {
                this.closeTimingBoxDiamondsTimer(),
                  (this._timingBoxDiamondsSecond = e);
                var t = cc.director.getScheduler();
                t.enableForTarget(this),
                  t.schedule(this.timingBoxDiamondsTimer, this, 1);
              }),
              (e.prototype.timingBoxDiamondsTimer = function () {
                (this._timingBoxDiamondsSecond -= 1),
                  this._timingBoxDiamondsSecond <= 0
                    ? (this.closeTimingBoxDiamondsTimer(),
                      r.default
                        .getInstance()
                        .setTimingBoxInfo(null, null, 0, 0, null, null, null),
                      cc.director.emit(
                        a.GameEvent.TimingBox_Diamonds_AD_Refresh,
                        this._timingBoxDiamondsSecond
                      ))
                    : cc.director.emit(
                        a.GameEvent.TimingBox_Diamonds_AD_Refresh,
                        this._timingBoxDiamondsSecond
                      );
              }),
              (e.prototype.closeTimingBoxDiamondsTimer = function () {
                cc.director
                  .getScheduler()
                  .unschedule(this.timingBoxDiamondsTimer, this),
                  (this._timingBoxDiamondsSecond = 0);
              }),
              (e.prototype.startTurntableTimer = function (e) {
                this.closeTurntableTimer(), (this._turntableSecond = e);
                var t = cc.director.getScheduler();
                t.enableForTarget(this),
                  t.schedule(this.turntableTimer, this, 1);
              }),
              (e.prototype.turntableTimer = function () {
                (this._turntableSecond -= 1),
                  this._turntableSecond <= 0
                    ? (this.closeTurntableTimer(),
                      r.default
                        .getInstance()
                        .setTurntableInfo(
                          0,
                          o.TURNTABLE_LEFT_SPIN_COUNT,
                          o.TURNTABLE_ADBONUS
                        ),
                      cc.director.emit(
                        a.GameEvent.Turntable_CD_Refresh,
                        this._turntableSecond
                      ))
                    : cc.director.emit(
                        a.GameEvent.Turntable_CD_Refresh,
                        this._turntableSecond
                      );
              }),
              (e.prototype.closeTurntableTimer = function () {
                cc.director
                  .getScheduler()
                  .unschedule(this.turntableTimer, this),
                  (this._turntableSecond = 0);
              }),
              (e.prototype.startOnlineTimer = function (e) {
                this.closeOnlineTimer(), (this._onlineSecond = e);
                var t = cc.director.getScheduler();
                t.enableForTarget(this), t.schedule(this.onlineTimer, this, 1);
              }),
              (e.prototype.onlineTimer = function () {
                (this._onlineSecond -= 1),
                  this._onlineSecond <= 0 &&
                    (this.closeOnlineTimer(),
                    i.default.getInstance().getTools().popupADReward());
              }),
              (e.prototype.closeOnlineTimer = function () {
                cc.director.getScheduler().unschedule(this.onlineTimer, this),
                  (this._onlineSecond = 0);
              }),
              (e.prototype.startADRewardTimer = function (e) {
                this.closeOnlineTimer(),
                  this.closeADRewardTimer(),
                  (this._adRewardSecond = e);
                var t = cc.director.getScheduler();
                t.enableForTarget(this),
                  t.schedule(this.adRewardTimer, this, 1);
              }),
              (e.prototype.adRewardTimer = function () {
                (this._adRewardSecond -= 1),
                  this._adRewardSecond <= 0 &&
                    (this.closeADRewardTimer(),
                    i.default.getInstance().getTools().popupADReward());
              }),
              (e.prototype.closeADRewardTimer = function () {
                cc.director.getScheduler().unschedule(this.adRewardTimer, this),
                  (this._adRewardSecond = 0);
              }),
              (e.prototype.getTimingBoxCoinsSecond = function () {
                return this._timingBoxCoinsSecond;
              }),
              (e.prototype.getTimingBoxDiamondsSecond = function () {
                return this._timingBoxDiamondsSecond;
              }),
              (e.prototype.getTurntableSecond = function () {
                return this._turntableSecond;
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = s), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "./GameDataManager": "GameDataManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    H5Test: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "3a70fnxmOZCjZyE4k4Zj6sc", "H5Test"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = (function () {
          function e() {}
          return (
            (e.init = function () {
              window.h5Test = e;
            }),
            (e.htmlCallJs = function () {
              console.log("\u7f51\u9875\u8c03\u7528JShtmlCallJS");
            }),
            (e.htmlCallJsParameter = function (e) {
              console.log("\u7f51\u9875\u8c03\u7528htmlCallJsParameter: " + e);
            }),
            (e.JSCallHtml = function () {
              window.JSCallHtml();
            }),
            (e.JSCallHtmlParameter = function () {
              window.JSCallHtmlParameter(11111);
            }),
            (e.htmlCallJsParameterCount = 0),
            e
          );
        })();
        (n.default = o), cc._RF.pop();
      },
      {},
    ],
    HallScene: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "8ce0aFNmJVMpaSVL3tvt5rv", "HallScene");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Script/Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/GameDataManager"),
          p = e("../Framework/Manager/GlobalTimerManager"),
          f = e("../Framework/Manager/RoomInfoManager"),
          h = e("../Framework/Manager/UserInfoManager"),
          g = e("../Framework/Native/NativeBridge"),
          m = e("../Framework/Utils/Utils"),
          _ = e("../Game/QuitGameView"),
          y = e("../Framework/Manager/TaskManager"),
          v = e("../Framework/Manager/AtlasResManager"),
          I = e("./activity/activityMatchPlayerView"),
          C = e("../Framework/Manager/CirculateManager"),
          k = e("./activity/activityHelp"),
          w = cc._decorator,
          P = w.ccclass,
          S = w.property,
          b = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprHeadPhoto = null),
                (t.labLv = null),
                (t.progressExp = null),
                (t.labNickName = null),
                (t.labExp = null),
                (t.labGold = null),
                (t.sprGold = null),
                (t.mainNode = null),
                (t.mainNodeScale = 0),
                (t.nodeIcon = null),
                (t.label_online_num = null),
                (t.label_box_num = null),
                (t.btn_receive = null),
                (t.node_time = null),
                (t.label_gold = null),
                (t.label_dia = null),
                (t.label_time = null),
                (t.node_btnOnlinereward = null),
                (t.node_btnSign = null),
                (t.node_btnTurn = null),
                (t.node_parent = null),
                (t.scroll_online = null),
                (t.node_room_parent = null),
                (t.node_top = null),
                (t.node_applet = null),
                (t.endTime = 0),
                (t.scroll_ContentPos = cc.v2(0, 0)),
                (t.btn_index = 0),
                (t.btn_max = 4),
                (t.startPos = null),
                (t.endPos = null),
                (t.isStart = !1),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                var e = this;
                console.log(
                  "\u7ed3\u675f\u52a0\u8f7d\uff1a " +
                    m.default.getCurTimeStamp()
                ),
                  v.default.getInstance().loadHallPrefab(),
                  g.default.preloadReward("loadReward"),
                  h.default.getInstance().isShowAppluck(!0),
                  g.default.closeBanner(),
                  g.default.nativeLog(
                    "\u5927\u5385\u573a\u666f\u52a0\u8f7d\u5b8c\u6bd5onload\uff0cts:" +
                      m.default.getCurTimeStamp()
                  );
                var t = g.default.getGameVersion(),
                  n = 0;
                t && (n = JSON.parse(t).version),
                  n > h.default.getInstance().getGameVersion() &&
                    (h.default.getInstance().setGameCount(0),
                    h.default.getInstance().setGameVersion(n)),
                  this.registerAllEvents(),
                  m.default.localStr(this.node),
                  d.default.getInstance().setSceneType(c.SceneType.Hall),
                  y.default.getInstance().initTask();
                var o = h.default.getInstance().getMyselfUserInfo();
                if (
                  (this.onUpdateHeadPhoto(o.getHeadPhotoIdx()),
                  this.onUpdateNickName(o.getNickName()),
                  this.onUpdateLevel(o.getLevel()),
                  this.onUpdateGoldNum(o.getGoldNum()),
                  this.onUpdateExp(o.getExp(), o.getLevelUpExp()),
                  this.checkPopupSign(),
                  this.checkPopupNoNetwork(),
                  this.updateTimeReward(),
                  this.updateSelectBg(2),
                  this.updateAppletIcon(),
                  l.default
                    .getInstance()
                    .playMusicWithPath(c.AudioType.BGM, !0, 0.8),
                  d.default.getInstance().getOpenApp() &&
                    (g.default.showNoAdmobInterstitial(c.ADType.coldSplashShow),
                    d.default.getInstance().setOpenApp(!1)),
                  this.schedule(function () {
                    e.updateOnlineNum(), e.updateBoxNum();
                  }, 1),
                  console.log("\u5173\u95edbanner"),
                  m.default.getUINeedScale(),
                  d.default.getInstance().getExitType() ==
                    c.MidwayQuitType.OutTime && this.showExitGame(),
                  d.default.getInstance().getIsAgain() &&
                    (f.default.getInstance().getGameMode() == c.GameMode.Local
                      ? this.loadRes(
                          s.HALL_PREFAB_PATH + "TransitionView",
                          cc.Prefab,
                          function (t) {
                            cc.instantiate(t).parent = e.node_parent;
                          }
                        )
                      : this.loadRes(
                          s.HALL_PREFAB_PATH + "RoomInfoView",
                          cc.Prefab,
                          function (t) {
                            cc.instantiate(t).parent = e.node_room_parent;
                          }
                        )),
                  d.default.getInstance().getOpenRoom() &&
                    (f.default.getInstance().getGameMode() == c.GameMode.Local
                      ? this.loadRes(
                          s.HALL_PREFAB_PATH + "LocalRoomView",
                          cc.Prefab,
                          function (t) {
                            cc.instantiate(t).parent = e.node_room_parent;
                          }
                        )
                      : this.loadRes(
                          s.HALL_PREFAB_PATH + "RoomInfoView",
                          cc.Prefab,
                          function (t) {
                            cc.instantiate(t).parent = e.node_room_parent;
                          }
                        ),
                    d.default.getInstance().setOpenRoom(!1)),
                  this.showHallIcon(),
                  this.scheduleOnce(function () {
                    d.default
                      .getInstance()
                      .setHallGoldPos(m.default.getWorldPosition(e.sprGold)),
                      e.checkPopupUpgrade();
                  }, 0),
                  this.scheduleOnce(function () {
                    var e = d.default.getInstance().getWinGoldQuit();
                    if (e > 0) {
                      d.default.getInstance().setWinGoldQuit(0);
                      var t = d.default.getInstance().getHallGoldPos();
                      d.default
                        .getInstance()
                        .getTools()
                        .playFlyEffect(
                          c.FlyEffectType.Coins,
                          t,
                          e,
                          function () {
                            var t = h.default.getInstance().getMyselfUserInfo();
                            t.setGoldNum(t.getGoldNum() + e);
                          }
                        );
                    }
                  }, 0.5),
                  p.default.getInstance().startOnlineTimer(s.AD_REWARD_CD_TIME),
                  this.reportUserInfo(),
                  h.default.getInstance().setIsEnterGame(1),
                  this.scroll_online.node.on(
                    cc.Node.EventType.TOUCH_START,
                    this.onTouchStart,
                    this,
                    !0
                  ),
                  this.scroll_online.node.on(
                    cc.Node.EventType.TOUCH_CANCEL,
                    this.cancel,
                    this,
                    !0
                  ),
                  this.scroll_online.node.on(
                    cc.Node.EventType.TOUCH_END,
                    this.cancel,
                    this,
                    !0
                  ),
                  C.default.getInstance().isPlayAgain &&
                    (this.loadRes(
                      s.HALL_PREFAB_PATH + "activity/activityView",
                      cc.Prefab,
                      function (t) {
                        cc.instantiate(t).parent = e.node_parent;
                      }
                    ),
                    (C.default.getInstance().isPlayAgain = !1)),
                  C.default.getInstance().isPlayMatch)
                ) {
                  for (
                    var a = C.default.getInstance().getActivityList(),
                      i = null,
                      r = 0;
                    r < a.length;
                    r++
                  )
                    C.default.getInstance().circulateActivity ==
                      a[r].activityType && (i = a[r]);
                  i && this.showActivityMatch(i),
                    (C.default.getInstance().isPlayMatch = !1);
                }
                C.default.getInstance().isActivitying &&
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "activity/promotionView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node;
                    }
                  ),
                  d.default.getInstance().isWin;
              }),
              (t.prototype.onTouchStart = function () {
                (this.startPos = this.scroll_online.getContentPosition()),
                  (this.isStart = !1),
                  console.log("onTouchStartAdd");
              }),
              (t.prototype.cancel = function () {
                console.log("endPos"),
                  this.scroll_online.stopAutoScroll(),
                  (this.endPos = this.scroll_online.getContentPosition()),
                  (this.isStart = !0);
              }),
              (t.prototype.updateOnlineNum = function () {
                var e = y.default.getInstance().getOnlineRewardInfo(),
                  t = h.default.getInstance().getOnlineTime(),
                  n = 0;
                for (var o in e)
                  e[o].taskStatus == c.TaskStatus.Task_NotCan &&
                    t >= e[o].time &&
                    n++;
                n > 0
                  ? ((this.label_online_num.string = n + ""),
                    (this.label_online_num.node.parent.active = !0))
                  : (this.label_online_num.node.parent.active = !1);
              }),
              (t.prototype.updateAppletIcon = function () {
                s.ISAPPLET &&
                  (this.node_applet.active = !d.default
                    .getInstance()
                    .getIsGetAppletReward());
              }),
              (t.prototype.updateTimeReward = function () {
                var e = h.default.getInstance().getTimeReward();
                m.default.getCurTimeStamp() > e
                  ? ((this.btn_receive.active = !0),
                    (this.node_time.active = !1))
                  : ((this.btn_receive.active = !1),
                    (this.node_time.active = !0),
                    (this.endTime = Math.ceil(
                      (e - m.default.getCurTimeStamp()) / 1e3
                    )),
                    this.updateTime(),
                    this.schedule(this.updateTime, 1));
              }),
              (t.prototype.updateTime = function () {
                this.endTime > 0
                  ? ((this.label_time.string = m.default.countDown(
                      this.endTime
                    )),
                    this.endTime--)
                  : (this.updateTimeReward(), this.unschedule(this.updateTime));
              }),
              (t.prototype.updateBoxNum = function () {
                var e = h.default.getInstance().getTimingBoxInfo();
                s.TIMINGBOX_AD_COUNT_LIMIT - e.coinsADCount > 0 ||
                s.TIMINGBOX_AD_COUNT_LIMIT - e.diamondsADCount > 0
                  ? ((this.label_box_num.string =
                      s.TIMINGBOX_AD_COUNT_LIMIT -
                      e.coinsADCount +
                      s.TIMINGBOX_AD_COUNT_LIMIT -
                      e.diamondsADCount +
                      ""),
                    (this.label_box_num.node.parent.active = !1))
                  : (this.label_box_num.node.parent.active = !1);
              }),
              (t.prototype.testProb = function () {
                for (var e = 0; e < 1e4; e++)
                  m.default.getDicePointsByProbability(3, 0.52);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Update_HeadPhoto,
                  this.onUpdateHeadPhoto,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Update_Nick_Name,
                    this.onUpdateNickName,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Update_Cur_Level,
                    this.onUpdateLevel,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Update_Gold_Num,
                    this.onUpdateGoldNum,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Update_Cur_Exp,
                    this.onUpdateExp,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Popup_Match_Player,
                    this.onMatchPlayer,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Guess_Size_UI,
                    this.onClickGuessSize,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Sign_View,
                    this.onShowSignView,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Play_Close_Audio,
                    this.onCloseAudio,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Select_Language,
                    this.updateLanguage,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Open_ActivityMain,
                    this.showActivityMain,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Close_Parent_Ui,
                    this.closeParentUI,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Show_Hall_Icon,
                    this.showHallIcon,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Update_Applet_Icon,
                    this.updateAppletIcon,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.showActivityMatch,
                    this.showActivityMatch,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.showActivityHelp,
                    this.showHelp,
                    this
                  );
              }),
              (t.prototype.showHallIcon = function () {
                (this.node_btnOnlinereward.active =
                  v.default.getInstance().isLoadHallPrefab),
                  (this.node_btnSign.active =
                    v.default.getInstance().isLoadHallPrefab),
                  (this.node_btnTurn.active =
                    v.default.getInstance().isLoadHallPrefab);
              }),
              (t.prototype.onCloseAudio = function () {
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click);
              }),
              (t.prototype.showActivityMatch = function (e) {
                var t = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "activity/activityMatchPlayerView",
                  cc.Prefab,
                  function (n) {
                    var o = cc.instantiate(n);
                    (o.parent = t.node_parent),
                      o.getComponent(I.default).initData(e);
                  }
                );
              }),
              (t.prototype.updateLanguage = function () {
                m.default.localStr(this.node);
              }),
              (t.prototype.reportUserInfo = function () {
                var e = h.default.getInstance().getMyselfUserInfo(),
                  t = {
                    event: c.BuriedPointKey.UserInfo,
                    nickName: e.getNickName(),
                    country: e.getCountryName(),
                    coins: e.getGoldNum(),
                    diamonds: e.getDiamondNum(),
                    level: e.getLevel(),
                  };
                u.default.getInstance().sendBuriedPointInfo(t);
              }),
              (t.prototype.checkPopupNovice = function () {
                var e = this;
                h.default.getInstance().getCompletedGuide() ||
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "NoviceView",
                    cc.Prefab,
                    function (t) {
                      var n = cc.instantiate(t);
                      (n.parent = e.node_parent), (n.zIndex = 10);
                    }
                  );
              }),
              (t.prototype.checkNewPlayReward = function () {
                var e = this;
                d.default.getInstance().getIsNewPlay() &&
                  (this.loadRes(
                    s.HALL_PREFAB_PATH + "NewPlayReward",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  ),
                  d.default.getInstance().setIsNewPlay(!1));
              }),
              (t.prototype.checkPopupSign = function () {
                d.default.getInstance().isFirstEnterGame() ||
                  h.default.getInstance().getSignInfo().isSignToday ||
                  this.onShowSignView();
              }),
              (t.prototype.onBtnActivityClick = function (e, t) {
                1 == parseInt(t)
                  ? u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.menuActivity,
                        actionName: c.BuriedTwoKey.menuActivityEntrance_1,
                      })
                  : u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.menuActivity,
                        actionName: c.BuriedTwoKey.menuActivityEntrance_2,
                      }),
                  h.default.getInstance().loadActivityRewardCount(),
                  h.default.getInstance().setOpenActivityTime(),
                  f.default.getInstance().setEntranceType(c.Entrance.Activity);
                var n = d.default.getInstance().getTools().getGlobalJson()
                    .info[0].newIsShowActivity,
                  o = g.default.getGameVersion();
                n && parseInt(o) > 2908 && g.default.openAHA();
              }),
              (t.prototype.showActivityClick = function () {
                var e = this;
                h.default.getInstance().loadActivityRewardCount(),
                  h.default.getInstance().setOpenActivityTime(),
                  f.default.getInstance().setEntranceType(c.Entrance.Activity);
                var t = d.default.getInstance().getTools().getGlobalJson()
                    .info[0].newIsShowActivity,
                  n = g.default.getGameVersion();
                t &&
                  parseInt(n) > 2908 &&
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "activity/activityInfo",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  );
              }),
              (t.prototype.showActivityMain = function () {
                var e = this;
                h.default.getInstance().loadActivityRewardCount(),
                  h.default.getInstance().setOpenActivityTime(),
                  f.default.getInstance().setEntranceType(c.Entrance.Activity);
                var t = d.default.getInstance().getTools().getGlobalJson()
                    .info[0].newIsShowActivity,
                  n = g.default.getGameVersion();
                t &&
                  parseInt(n) > 2908 &&
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "activity/activityMain",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  );
              }),
              (t.prototype.onBtnOnlineClick = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "OnlineRewardView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Online,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Online,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openOnlineGame,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openOnlineReward,
                    });
              }),
              (t.prototype.onShowSignView = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "SignView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Sign,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Sign,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openDailySign,
                    });
              }),
              (t.prototype.onBtnTaskClick = function () {
                var e = this;
                d.default.getInstance().getTools().showNoNetWorkTip() &&
                  (this.loadRes(
                    s.HALL_PREFAB_PATH + "TaskView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Task,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Task,
                    }));
              }),
              (t.prototype.checkPopupNoNetwork = function () {
                var e = this;
                g.default.getNetworkStatus() != c.NetworkStatus.No ||
                  d.default.getInstance().isPopupNoNetwork() ||
                  (this.loadRes(
                    s.HALL_PREFAB_PATH + "NoNetworkView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  ),
                  d.default.getInstance().setPopupNoNetwork(!0));
              }),
              (t.prototype.checkPopupUpgrade = function () {}),
              (t.prototype.onUpdateHeadPhoto = function (e) {
                var t = this;
                this.loadRes(
                  s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + e,
                  cc.SpriteFrame,
                  function (e) {
                    t.sprHeadPhoto.spriteFrame = e;
                  }
                );
              }),
              (t.prototype.onUpdateNickName = function (e) {
                this.labNickName.string = e;
              }),
              (t.prototype.onUpdateLevel = function (e) {
                this.labLv.string = "" + e;
              }),
              (t.prototype.onUpdateGoldNum = function (e) {
                this.labGold.string = "" + e;
              }),
              (t.prototype.onUpdateExp = function (e, t) {
                (this.labExp.string = e + "/" + t),
                  (this.progressExp.progress = e / t);
              }),
              (t.prototype.onClickHeadPhoto = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  d.default.getInstance().getIsOpenUser() ||
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "UserInfoView",
                      cc.Prefab,
                      function (t) {
                        (cc.instantiate(t).parent = e.node_parent),
                          d.default.getInstance().setIsOpenUser(!0);
                      }
                    ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openUserInfo,
                    });
              }),
              (t.prototype.onClickGoldAdd = function () {
                this.onClickShop(c.ShopShowType.Gold),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.coinAddBtnClick,
                    });
              }),
              (t.prototype.onClickDiamondAdd = function () {
                this.onClickShop(c.ShopShowType.Dimaond);
              }),
              (t.prototype.onBtnShopClick = function () {
                g.default.preInterstitialReady(c.ADType.CloseShop_Insert),
                  this.onClickShop(c.ShopShowType.Gold);
              }),
              (t.prototype.onClickShop = function (e) {
                this.updateSelectBg(1),
                  d.default
                    .getInstance()
                    .getTools()
                    .popupShopView(e, null, this.node_parent),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Shop,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Shop,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openShop,
                    });
              }),
              (t.prototype.onScrollViewCallBack = function () {
                var e = this.node_top.width / 6;
                if ((this.btn_max--, this.isStart)) {
                  console.log("_scrolling");
                  var t = this.scroll_online.getContentPosition();
                  switch (
                    (console.log(
                      "startPos: " +
                        this.startPos.x +
                        "----endPos: " +
                        this.endPos.x
                    ),
                    this.endPos.x - this.startPos.x > e &&
                    this.endPos.x - this.startPos.x > 0
                      ? (this.btn_index--,
                        this.btn_index < 0 && (this.btn_index = 0),
                        console.log("this.index--: " + this.btn_index))
                      : this.endPos.x - this.startPos.x < -e &&
                        this.endPos.x - this.startPos.x < 0 &&
                        (this.btn_index++,
                        console.log("this.index++: " + this.btn_index)),
                    this.btn_index)
                  ) {
                    case 0:
                      this.scroll_online.scrollToLeft(0.1);
                      break;
                    case 1:
                      this.scroll_online.scrollToPercentHorizontal(0.5, 0.1);
                      break;
                    case 2:
                      this.scroll_online.scrollToRight(0.1);
                  }
                  (this.isStart = !1), (this.scroll_ContentPos = t);
                }
              }),
              (t.prototype.onClickFriends = function () {}),
              (t.prototype.onClickRankList = function () {}),
              (t.prototype.onClickSetup = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "GameSettingView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openSettings,
                    });
              }),
              (t.prototype.onClickPlayOnline = function () {
                var e = this;
                d.default.getInstance().getTools().showNoNetWorkTip() &&
                  (f.default.getInstance().setEntranceType(c.Entrance.Room),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  f.default.getInstance().setGameMode(c.GameMode.Online),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "RoomInfoView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_room_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameType,
                      gameType: c.GameMode.Online,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameType,
                      actionName: c.BuriedPointSecondKey.gameType,
                      value: c.GameMode.Online,
                    }));
              }),
              (t.prototype.onClickPlayWithComputer = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  f.default.getInstance().setEntranceType(c.Entrance.Room),
                  f.default.getInstance().setGameMode(c.GameMode.Computer),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "computerRoomView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_room_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameType,
                      gameType: c.GameMode.Computer,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.GameType,
                      actionName: c.BuriedPointSecondKey.gameType,
                      value: c.GameMode.Computer,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openRobotGame,
                    });
              }),
              (t.prototype.onClickPlayWithLocal = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  f.default.getInstance().setEntranceType(c.Entrance.Room),
                  f.default.getInstance().setGameMode(c.GameMode.Local),
                  f.default.getInstance().setRoomMode(c.GameRoomMode.Classic),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "LocalRoomView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_room_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.LocalGameClick,
                      value: c.GameMode.Local,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openLocalGame,
                    }),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  f.default.getInstance().setGameMode(c.GameMode.Local),
                  f.default.getInstance().setRoomMode(c.GameRoomMode.Classic),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.LocalGameClick,
                      value: c.GameMode.Local,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openLocalGame,
                    });
              }),
              (t.prototype.onClickTimeReward = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "TimingBoxView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.TimingBox,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.TimingBox,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openLuckBox,
                    });
              }),
              (t.prototype.onClickAdRecharge = function () {}),
              (t.prototype.onClickTurntable = function () {
                var e = this;
                g.default.preInterstitialReady(c.ADType.CloseLuckyWheel_Insert),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  this.node_parent.removeAllChildren(),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "turntable/TurntableView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_room_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Turntable,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Turntable,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openLuckWheel,
                    }),
                  this.updateSelectBg(2);
              }),
              (t.prototype.onClickGuessSize = function () {
                var e = this;
                d.default.getInstance().getTools().showNoNetWorkTip() &&
                  (this.node_parent.removeAllChildren(),
                  g.default.preInterstitialReady(
                    c.ADType.CloseGuessSize_Insert
                  ),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "guess_size/GuessSizeView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_room_parent;
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.GuessSize,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.GuessSize,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.openFeatureFromHall,
                      actionName: c.BuriedTwoKey.openGuessGame,
                    }),
                  this.updateSelectBg(1));
              }),
              (t.prototype.onClickMainClick = function () {
                this.node_parent.removeAllChildren(), this.updateSelectBg(0);
              }),
              (t.prototype.onMatchPlayer = function () {
                var e = this;
                console.log(
                  "\u51c6\u5907\u5f00\u59cb\u8fdb\u5165\u5339\u914d\u754c\u9762"
                ),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "MatchPlayerView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node_top;
                    }
                  );
              }),
              (t.prototype.onClickQuit = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  g.default.preInterstitialReady(c.ADType.Hall_Quit_Insert),
                  this.loadRes(
                    s.GAME_PREFAB_PATH + "QuitGameView",
                    cc.Prefab,
                    function (t) {
                      var n = cc.instantiate(t);
                      (n.parent = e.node_parent),
                        n.getComponent(_.default).setInfo(function (e) {
                          e == c.PopupButtonClickType.Cancel
                            ? (u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedPointKey.CommonClick,
                                  clickType: c.ButtonClickType.QuitGameCancel,
                                }),
                              u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedPointKey.CommonClick,
                                  actionName: c.BuriedPointSecondKey.clickType,
                                  value: c.ButtonClickType.QuitGameCancel,
                                }))
                            : (u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedPointKey.CommonClick,
                                  clickType: c.ButtonClickType.QuitGameYes,
                                }),
                              u.default
                                .getInstance()
                                .sendBuriedPointInfo({
                                  event: c.BuriedPointKey.CommonClick,
                                  actionName: c.BuriedPointSecondKey.clickType,
                                  value: c.ButtonClickType.QuitGameYes,
                                }),
                              cc.game.end());
                        });
                    }
                  ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.QuitGame,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.QuitGame,
                    });
              }),
              (t.prototype.onShowPopularView = function () {
                var e = this;
                d.default.getInstance().getTools().getLockChargeSkinInfos()
                  .length > 0 &&
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "PopularSkinsView",
                    cc.Prefab,
                    function (t) {
                      var n = cc.instantiate(t);
                      (n.parent = e.node_parent), (n.zIndex = 5);
                    }
                  );
              }),
              (t.prototype.onBtnEnterSnakersClick = function () {
                h.default.getInstance().generateGameUser(),
                  f.default.getInstance().setEntryGold(500),
                  f.default.getInstance().caculatePlayerWinGold(),
                  h.default.getInstance().deductEntryGold(),
                  cc.director.loadScene("Snakers_and_ladders");
              }),
              (t.prototype.onBtnEnterSelectGold = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "SelectGold",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                ),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.Snakers,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.Snakers,
                    });
              }),
              (t.prototype.showExitGame = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "ExitGame",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                );
              }),
              (t.prototype.onBtnTest = function () {}),
              (t.prototype.onBtnOpenAppluck = function () {
                g.default.openAHA();
              }),
              (t.prototype.onBtnTESTAHAGame = function () {
                g.default.activityPlayGame(JSON.stringify("1111"));
              }),
              (t.prototype.onBtnReceiveClick = function () {
                var e = this;
                g.default.watchVideo(function () {
                  var t = d.default.getInstance().getHallGoldPos();
                  d.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(c.FlyEffectType.Coins, t, 3e3, function () {
                      var e = h.default.getInstance().getMyselfUserInfo();
                      e.setGoldNum(e.getGoldNum() + 1e3);
                    }),
                    h.default
                      .getInstance()
                      .setTimeReward(m.default.getCurTimeStamp() + 36e5),
                    e.updateTimeReward();
                }, c.ADType.TimingBoxGetReward);
              }),
              (t.prototype.updateSelectBg = function () {}),
              (t.prototype.closeParentUI = function () {
                d.default.getInstance().setIsOpenUser(!1),
                  this.node_parent.removeAllChildren(),
                  this.updateSelectBg(2);
              }),
              (t.prototype.onBtnLoadBundle1Prefab = function () {
                var e = this;
                cc.assetManager.loadBundle(
                  "https://h5games.com/Bundle",
                  function (t, n) {
                    n.load("Prefab/test", function (t, n) {
                      cc.instantiate(n).parent = e.node_parent;
                    });
                  }
                );
              }),
              (t.prototype.onBtnLoadBundle2Prefab = function () {
                var e = this;
                cc.assetManager.loadBundle("BundleTest", function (t, n) {
                  n.load("Prefab/test", function (t, n) {
                    cc.instantiate(n).parent = e.node_parent;
                  });
                });
              }),
              (t.prototype.onBtnTurnClick = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "turntable/TurntableView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_room_parent;
                  }
                );
              }),
              (t.prototype.onBtnAddAppletGuideClick = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "addGuideView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_room_parent;
                  }
                );
              }),
              (t.prototype.onBtnCupClick = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "activity/activityView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node_parent;
                  }
                );
              }),
              (t.prototype.showHelp = function (e) {
                var t = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "activity/activityHelp",
                  cc.Prefab,
                  function (n) {
                    var o = cc.instantiate(n);
                    (o.parent = t.node),
                      o.getComponent(k.default).updateReward(e);
                  }
                );
              }),
              (t.prototype.onBtnDownLoad = function () {
                var e = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "downLoadView",
                  cc.Prefab,
                  function (t) {
                    cc.instantiate(t).parent = e.node;
                  }
                );
              }),
              (t.prototype.onBtnTestClick = function () {
                var e = this;
                (C.default.getInstance().circulateActivity =
                  c.circulateActivity.roadblock),
                  (C.default.getInstance().First = !0),
                  (C.default.getInstance().rankIndex = 1),
                  (C.default.getInstance().competitionList = [1, 1]),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "activity/promotionView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node;
                    }
                  );
              }),
              i([S(cc.Sprite)], t.prototype, "sprHeadPhoto", void 0),
              i([S(cc.Label)], t.prototype, "labLv", void 0),
              i([S(cc.ProgressBar)], t.prototype, "progressExp", void 0),
              i([S(cc.Label)], t.prototype, "labNickName", void 0),
              i([S(cc.Label)], t.prototype, "labExp", void 0),
              i([S(cc.Label)], t.prototype, "labGold", void 0),
              i([S(cc.Node)], t.prototype, "sprGold", void 0),
              i([S(cc.Node)], t.prototype, "mainNode", void 0),
              i([S(Number)], t.prototype, "mainNodeScale", void 0),
              i([S(cc.Node)], t.prototype, "nodeIcon", void 0),
              i([S(cc.Label)], t.prototype, "label_online_num", void 0),
              i([S(cc.Label)], t.prototype, "label_box_num", void 0),
              i([S(cc.Node)], t.prototype, "btn_receive", void 0),
              i([S(cc.Node)], t.prototype, "node_time", void 0),
              i([S(cc.Label)], t.prototype, "label_gold", void 0),
              i([S(cc.Label)], t.prototype, "label_dia", void 0),
              i([S(cc.Label)], t.prototype, "label_time", void 0),
              i([S(cc.Node)], t.prototype, "node_btnOnlinereward", void 0),
              i([S(cc.Node)], t.prototype, "node_btnSign", void 0),
              i([S(cc.Node)], t.prototype, "node_btnTurn", void 0),
              i([S(cc.Node)], t.prototype, "node_parent", void 0),
              i([S(cc.ScrollView)], t.prototype, "scroll_online", void 0),
              i([S(cc.Node)], t.prototype, "node_room_parent", void 0),
              i([S(cc.Node)], t.prototype, "node_top", void 0),
              i([S(cc.Node)], t.prototype, "node_applet", void 0),
              i([P], t)
            );
          })(r.default);
        (n.default = b), cc._RF.pop();
      },
      {
        "../../Script/Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AtlasResManager": "AtlasResManager",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/CirculateManager": "CirculateManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/GlobalTimerManager": "GlobalTimerManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/TaskManager": "TaskManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "../Game/QuitGameView": "QuitGameView",
        "./activity/activityHelp": "activityHelp",
        "./activity/activityMatchPlayerView": "activityMatchPlayerView",
      },
    ],
    HeadPhotoItem: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "d56eaiQ2spO+Lq5eXQcecps", "HeadPhotoItem");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/UserInfoManager"),
          u = cc._decorator,
          d = u.ccclass,
          p = u.property,
          f = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.nodeHeadPhotos = []),
                (t.sprHeadPhotos = []),
                (t.sprSelects = []),
                (t._headPhotoIdxArray = null),
                (t._selectHeadPhotoIdx = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.User_Info_Select_HeadPhoto,
                  this.onSelectHeadPhoto,
                  this
                );
              }),
              (t.prototype.setInfo = function (e) {
                var t = this;
                this._headPhotoIdxArray = e;
                for (
                  var n = l.default.getInstance().getMyselfUserInfo(),
                    o = function (o) {
                      if (o < e.length) {
                        var i = e[o];
                        i == n.getHeadPhotoIdx() &&
                          (a.sprSelects[o].active = !0),
                          a.loadRes(
                            s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + i,
                            cc.SpriteFrame,
                            function (e) {
                              t.sprHeadPhotos[o].spriteFrame = e;
                            }
                          );
                      } else a.nodeHeadPhotos[o].active = !1;
                    },
                    a = this,
                    i = 0;
                  i < this.sprHeadPhotos.length;
                  i++
                )
                  o(i);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.onClickSelect = function (e, t) {
                for (
                  var n = parseInt(t), o = 0;
                  o < this.sprSelects.length;
                  o++
                )
                  this.sprSelects[o].active = n == o;
                (this._selectHeadPhotoIdx = this._headPhotoIdxArray[n]),
                  cc.director.emit(
                    c.GameEvent.User_Info_Select_HeadPhoto,
                    this._selectHeadPhotoIdx
                  );
              }),
              (t.prototype.onSelectHeadPhoto = function (e) {
                if (this._headPhotoIdxArray.indexOf(e) == s.ARRAY_ELE_NOT_EXIST)
                  for (var t = 0; t < this.sprSelects.length; t++)
                    this.sprSelects[t].active = !1;
              }),
              i([p(cc.Node)], t.prototype, "nodeHeadPhotos", void 0),
              i([p(cc.Sprite)], t.prototype, "sprHeadPhotos", void 0),
              i([p(cc.Node)], t.prototype, "sprSelects", void 0),
              i([d], t)
            );
          })(r.default);
        (n.default = f), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
      },
    ],
    LocalRoomView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "23904fmfDxHoL8duSYa0IUK", "LocalRoomView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Manager/UserInfoManager"),
          p = e("../Framework/Native/NativeBridge"),
          f = e("../Framework/Utils/Utils"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_player_list = []),
                (t.btnPlayer = []),
                (t.node_select_base = null),
                (t.labelNameList = []),
                (t.img_twe = null),
                (t.img_classic = null),
                (t.img_four = null),
                (t.labelOut_txt = []),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                f.default.localStr(this.node),
                  d.default.getInstance().isShowAppluck(!1),
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.localGameSelectScreen,
                      actionName: c.BuriedTwoKey.selectScreenShow,
                    }),
                  u.default.getInstance().setLocalInfo(0, !1, !1),
                  u.default.getInstance().setLocalInfo(2, !1, !1),
                  this.updateView(),
                  p.default.showBanner(),
                  this.updateBtnStatus(2);
              }),
              (t.prototype.updateView = function () {
                for (
                  var e = this,
                    t = u.default.getInstance().getLocalInfo(),
                    n = "",
                    o = "Local_nobody",
                    a = function (a) {
                      t[a]
                        ? (t[a].isNull
                            ? ((i.img_player_list[a].node.active = !1),
                              (n = ""),
                              (o = "Local_nobody"))
                            : 0 == t[a].isComputer
                            ? ((i.img_player_list[a].node.active = !0),
                              (n = "img_local_play"),
                              (o = "Local_human"))
                            : ((i.img_player_list[a].node.active = !0),
                              (n = "img_local_computer"),
                              (o = "Local_computer")),
                          "" != n &&
                            i.loadRes(
                              s.LOCAL + n,
                              cc.SpriteFrame,
                              function (t) {
                                e.img_player_list[a].spriteFrame = t;
                              }
                            ))
                        : ((i.img_player_list[a].node.active = !1),
                          (o = "Local_nobody")),
                        (i.labelNameList[a].string = f.default.replaceStr(o));
                    },
                    i = this,
                    r = 0;
                  r < 4;
                  r++
                )
                  a(r);
              }),
              (t.prototype.onBtnSelectPlayer = function (e, t) {
                var n = u.default.getInstance().getLocalInfo(),
                  o = parseInt(t);
                n[o]
                  ? n[o].isNull
                    ? u.default.getInstance().setLocalInfo(o, !1, !1)
                    : 0 == n[o].isComputer
                    ? u.default.getInstance().setLocalInfo(o, !0, !1)
                    : u.default.getInstance().deleLocalInfo(o)
                  : u.default.getInstance().setLocalInfo(o, !1, !1),
                  this.updateView();
              }),
              (t.prototype.onBtnPlayerClick = function (e, t) {
                var n = parseInt(t);
                if (2 == n) {
                  for (var o = 0; o < 4; o++)
                    u.default.getInstance().deleLocalInfo(o);
                  u.default.getInstance().setLocalInfo(0, !1, !1),
                    u.default.getInstance().setLocalInfo(2, !1, !1);
                } else
                  for (o = 0; o < 4; o++)
                    n > o
                      ? u.default.getInstance().setLocalInfo(o, !1, !1)
                      : u.default.getInstance().deleLocalInfo(o);
                for (
                  this.updateView(), this.updateBtnStatus(n), o = 0;
                  o < this.labelOut_txt.length;
                  o++
                )
                  this.labelOut_txt[o].color =
                    n == o + 2
                      ? new cc.Color(145, 78, 0)
                      : new cc.Color(0, 106, 169);
              }),
              (t.prototype.updateBtnStatus = function (e) {
                var t = this;
                2 == e
                  ? (this.loadRes(
                      "img_local_yellow_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_twe.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_classic.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_four.spriteFrame = e;
                      }
                    ))
                  : 3 == e
                  ? (this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_twe.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_yellow_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_classic.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_four.spriteFrame = e;
                      }
                    ))
                  : (this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_twe.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_blue_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_classic.spriteFrame = e;
                      }
                    ),
                    this.loadRes(
                      "img_local_yellow_bg",
                      cc.SpriteFrame,
                      function (e) {
                        t.img_four.spriteFrame = e;
                      }
                    ));
              }),
              (t.prototype.onBtnPlayClick = function () {
                var e = this,
                  t = u.default.getInstance().getLocalInfo(),
                  n = !1;
                if (Object.keys(t).length < 2) this.moveSelectBase();
                else {
                  for (var o in (p.default.watchVideo(function () {},
                  "localPlay_Insert"),
                  u.default.getInstance().setFristEnterGame(!1),
                  t))
                    t[o].isComputer || (n = !0);
                  if (n) {
                    if (!u.default.getInstance().getIsNewPlay()) {
                      var a = u.default
                        .getInstance()
                        .getTools()
                        .getGlobalJson();
                      f.default.getRandomNum(1, 100) <
                        a.info[0].show_local_insert &&
                        p.default.watchVideo(function () {},
                        c.ADType.Local_Insert);
                    }
                    d.default.getInstance().localGenerateGameUser(),
                      l.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: c.BuriedPointKey.LocalGameTypePlay,
                          value: Object.keys(t).length,
                        });
                    var i = {
                      gameType: "1",
                      playerCount: Object.keys(t).length,
                    };
                    l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedOneKey.localGameSelectScreen,
                        actionName: c.BuriedTwoKey.playBtnClick,
                        value: i,
                      }),
                      p.default.preInterstitialReady(c.ADType.LocalPlay),
                      this.loadRes(
                        s.HALL_PREFAB_PATH + "TransitionView",
                        cc.Prefab,
                        function (t) {
                          cc.instantiate(t).parent = e.node;
                        }
                      );
                  } else this.moveSelectBase();
                }
              }),
              (t.prototype.moveSelectBase = function () {
                this.node_select_base.runAction(
                  cc.sequence(
                    cc.moveTo(0.08, cc.v2(-20, 0)),
                    cc.moveTo(0.08, cc.v2(20, 0)),
                    cc.moveTo(0.08, cc.v2(-20, 0)),
                    cc.moveTo(0.08, cc.v2(20, 0)),
                    cc.moveTo(0.08, cc.v2(0, 0))
                  )
                );
              }),
              (t.prototype.onBtnCloseClick = function () {
                var e = this;
                l.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: c.BuriedOneKey.localGameSelectScreen,
                    actionName: c.BuriedTwoKey.exitBtnClick,
                  }),
                  d.default.getInstance().isShowAppluck(!0),
                  p.default.watchVideo(function () {
                    p.default.closeBanner(),
                      cc.director.emit(c.GameEvent.Close_Parent_Ui),
                      e.onClose();
                  }, c.ADType.Local_Insert);
              }),
              i([m(cc.Sprite)], t.prototype, "img_player_list", void 0),
              i([m(cc.Node)], t.prototype, "btnPlayer", void 0),
              i([m(cc.Node)], t.prototype, "node_select_base", void 0),
              i([m(cc.Label)], t.prototype, "labelNameList", void 0),
              i([m(cc.Sprite)], t.prototype, "img_twe", void 0),
              i([m(cc.Sprite)], t.prototype, "img_classic", void 0),
              i([m(cc.Sprite)], t.prototype, "img_four", void 0),
              i([m(cc.LabelOutline)], t.prototype, "labelOut_txt", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    LoginScene: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "1b512rM5sFKhLn6aaunPtK4", "LoginScene");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/GameDataManager"),
          p = e("../Framework/Manager/UserInfoManager"),
          f = e("../Framework/Native/NativeBridge"),
          h = e("../Framework/Utils/Utils"),
          g = cc._decorator,
          m = g.ccclass,
          _ =
            (g.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  var e = this;
                  f.default.nativeLog(
                    "\u767b\u5f55\u573a\u666f\u52a0\u8f7d\u5b8c\u6bd5onload\uff0cts:" +
                      h.default.getCurTimeStamp()
                  ),
                    this.registerAllEvents(),
                    d.default.getInstance().setSceneType(c.SceneType.Login),
                    p.default.getInstance().genMyselfUserId(),
                    this.loadRes(
                      s.LOGIN_PREFAB_PATH + "LoginUserInfoView",
                      cc.Prefab,
                      function (t) {
                        cc.instantiate(t).parent = e.node;
                      }
                    );
                }),
                (t.prototype.registerAllEvents = function () {
                  this.registerEvent(
                    c.GameEvent.User_Info_Modify_Success,
                    this.onLoginSuccess,
                    this
                  );
                }),
                (t.prototype.start = function () {}),
                (t.prototype.onLoginSuccess = function () {
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.Register,
                      registerType: c.RegisterType.Guest,
                    }),
                    l.default.getInstance().stopAllAudio(),
                    cc.director.loadScene("Hall");
                }),
                i([m], t)
              );
            })(r.default));
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    LuckManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "190603MFRlDCLe5QAa91KIZ", "LuckManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("../Utils/Utils"),
          r = e("./ChessManager"),
          s = e("./GameDataManager"),
          c = e("./MapGridManager"),
          l = e("./RobotManager"),
          u = e("./RoomInfoManager"),
          d = e("./UserInfoManager"),
          p = (function () {
            function e() {
              (this._curLuck = 1),
                (this._gameDifficultyJson = null),
                (this._canEnterEndCount = 4),
                (this._gameDifficultyJson = s.default
                  .getInstance()
                  .getTools()
                  .getGameDifficultyJson());
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.checkLuckLimit = function (e, t) {
                return e
                  ? !(
                      i.default.isEqualFloatNumber(
                        t,
                        this._gameDifficultyJson.luckMax
                      ) || t < this._gameDifficultyJson.luckMax
                    )
                  : !(
                      i.default.isEqualFloatNumber(
                        t,
                        this._gameDifficultyJson.luckMin
                      ) || t > this._gameDifficultyJson.luckMin
                    );
              }),
              (e.prototype.setLuckValue = function (e, t, n, o) {
                t == a.LuckChangeType.Eate || t == a.LuckChangeType.beEaten
                  ? (e.setLuck(n), e.addTotalChangeLuckValue(t, o))
                  : (e.setActualLuck(n),
                    d.default.getInstance().setLuckInfo(n));
              }),
              (e.prototype.getLuckValue = function (e, t) {
                return e.isMyself()
                  ? t == a.LuckChangeType.Eate || t == a.LuckChangeType.beEaten
                    ? e.getLuck()
                    : e.getActualLuck()
                  : e.getLuck();
              }),
              (e.prototype.checkTotoalChangeLuckValueLimit = function (e, t) {
                if (t == a.LuckChangeType.Eate) {
                  var n = e.getTotalChangeLuckValue(t);
                  return !(
                    !i.default.isEqualFloatNumber(
                      n,
                      this._gameDifficultyJson.eateOtherMinusMost
                    ) && n < this._gameDifficultyJson.eateOtherMinusMost
                  );
                }
                return (
                  t == a.LuckChangeType.beEaten &&
                  ((n = e.getTotalChangeLuckValue(t)),
                  !(
                    !i.default.isEqualFloatNumber(
                      n,
                      this._gameDifficultyJson.beEatenAddMost
                    ) && n < this._gameDifficultyJson.beEatenAddMost
                  ))
                );
              }),
              (e.prototype.changeLuck = function (e, t) {
                d.default.getInstance().getGameTotalRounds();
                var n = d.default.getInstance().getUserByIndex(e);
                if (!this.checkTotoalChangeLuckValueLimit(n, t)) {
                  var o = !1,
                    i = 0;
                  t == a.LuckChangeType.Win
                    ? ((o = !1),
                      (i = this._gameDifficultyJson.winMinusLuck),
                      d.default.getInstance().setContinuityLostCount(0))
                    : t == a.LuckChangeType.Lost
                    ? ((o = !0),
                      (i = this._gameDifficultyJson.lostAddLuck),
                      d.default
                        .getInstance()
                        .setContinuityLostCount(
                          d.default.getInstance().getContinuityLostCount() + 1
                        ))
                    : t == a.LuckChangeType.Eate
                    ? ((o = !1),
                      (i = this._gameDifficultyJson.eateOtherMinusLuck))
                    : t == a.LuckChangeType.beEaten &&
                      ((o = !0), (i = this._gameDifficultyJson.beEatenAddLuck));
                  var r,
                    s = this.getLuckValue(n, t);
                  if (((r = o ? s + i : s - i), !this.checkLuckLimit(o, r)))
                    if (n.isMyself()) {
                      if (
                        (this.setLuckValue(n, t, r, i),
                        t == a.LuckChangeType.Win || t == a.LuckChangeType.Lost)
                      ) {
                        var c = this.getLevelDiff(),
                          l = this.getContinuityLostLuckValue(c.min, c.max);
                        this.setLuckValue(n, t, l, i);
                      }
                    } else
                      !n.isRobot() ||
                        (t != a.LuckChangeType.Eate &&
                          t != a.LuckChangeType.beEaten) ||
                        (n.setLuck(r), n.addTotalChangeLuckValue(t, i));
                }
              }),
              (e.prototype.getContinuityLostLuckValue = function (e, t) {
                var n = Math.ceil(((e + t) / 2) * 10) / 10;
                console.log(
                  "\u8ba1\u7b97\u7b49\u7ea7\u96be\u5ea6\u5e73\u5747\u5e78\u8fd0\u503c\u8303\u56f4\uff1a" +
                    n
                );
                var o = d.default.getInstance().getContinuityLostCount(),
                  a = 0;
                return (
                  o > 5
                    ? (a = 100)
                    : o > 4
                    ? (a = 90)
                    : o > 3
                    ? (a = 80)
                    : o > 2
                    ? (a = 70)
                    : o > 1 && (a = 60),
                  i.default.getRandomNum(1, 100) < a ? 1.5 : n
                );
              }),
              (e.prototype.isPlayerChessExceedHalf = function (e) {
                for (
                  var t = this._gameDifficultyJson.exceedHalfGridCount,
                    n = r.default.getInstance().getPlayerAllChess(e),
                    o = 0;
                  o < n.length;
                  o++
                )
                  if (n[o].getWalkSteps() > t) return !0;
                return !1;
              }),
              (e.prototype.isPlayerChessExceedCircle = function (e) {
                for (
                  var t = this._gameDifficultyJson.exceedCircleGridCount,
                    n = r.default.getInstance().getPlayerAllChess(e),
                    o = 0,
                    a = 0;
                  a < n.length;
                  a++
                )
                  o += n[a].getWalkSteps();
                return o > t;
              }),
              (e.prototype.getRobot = function (e) {
                var t = (1.1 * e) / this._gameDifficultyJson.sixPointsDivide;
                return i.default.getDicePointsByProbability(6, t);
              }),
              (e.prototype.getDefaultDicePoints = function (e, t) {
                void 0 === e && (e = !1), void 0 === t && (t = 1);
                var n = 1,
                  a = d.default.getInstance().getGameTotalRounds();
                if (e && a <= 3) n = this.robatDicePoint(t);
                else {
                  var r = d.default.getInstance().getSkinInfo(),
                    c = s.default
                      .getInstance()
                      .getTools()
                      .getSkinInfo(r.selectSkin),
                    l = o.DICE_MAX_POINTS;
                  0 == s.default.getInstance().getRoundCount() &&
                    (l = Math.ceil(
                      o.DICE_MAX_POINTS + o.DICE_MAX_POINTS * c.skinBuffValue
                    )),
                    (n = i.default.getRandomNum(1, l)) >= o.DICE_MAX_POINTS &&
                      (n = o.DICE_MAX_POINTS);
                }
                return n;
              }),
              (e.prototype.robatDicePoint = function (e) {
                console.log("\u4eba\u673a\u6447\u585e\u5b50");
                for (
                  var t = r.default.getInstance().getPlayerAllChess(e),
                    n = [1, 2, 3, 4, 5, 6],
                    a = 0;
                  a < t.length;
                  a++
                )
                  for (var s = t[a], c = 6; c >= 1; c--) {
                    var l = s.canEateOther(c);
                    l &&
                      l.getOwnerPlayerIndex() ==
                        d.default
                          .getInstance()
                          .getMyselfUserInfo()
                          .getPlayerIndex() &&
                      n.indexOf(c) != o.ARRAY_ELE_NOT_EXIST &&
                      n.splice(n.indexOf(c), 1);
                  }
                return (
                  console.log(
                    "\u53ef\u4ee5\u968f\u673a\u7684\u6570\u5b57\uff1a " + n
                  ),
                  i.default.getRandomArrayElements(n, 1)[0]
                );
              }),
              (e.prototype.getNotSixDicePoints = function () {
                return i.default.getRandomNum(1, 5);
              }),
              (e.prototype.getDicePoints = function (e, t, n, o) {
                void 0 === o && (o = !1),
                  console.log("\u73a9\u5bb6\u6447\u585e\u5b50");
                var s = 0,
                  l = (u.default.getInstance().getRoomMode(), e.getLuck()),
                  p = e.getPlayerIndex(),
                  f = d.default.getInstance().getGameTotalRounds();
                if (t)
                  if (
                    u.default.getInstance().getRoomMode() ==
                      a.GameRoomMode.Classic &&
                    f < 4 &&
                    o
                  )
                    s =
                      1 == n
                        ? i.default.getRandomNum(1, 100) <= 40
                          ? 6
                          : i.default.getRandomNum(1, 6)
                        : 2 == n
                        ? i.default.getRandomNum(1, 100) <= 65
                          ? 6
                          : i.default.getRandomNum(1, 6)
                        : 3 == n
                        ? i.default.getRandomNum(1, 100) <= 85
                          ? 6
                          : i.default.getRandomNum(1, 6)
                        : 6;
                  else {
                    var h = (n * l) / this._gameDifficultyJson.sixPointsDivide;
                    (s = i.default.getDicePointsByProbability(6, h)),
                      cc.director.emit(
                        a.GameEvent.Refresh_Player_Luck_Info,
                        p,
                        l,
                        t,
                        h,
                        0
                      );
                  }
                else {
                  var g = this.getCanEateOtherChess(e, l);
                  r.default
                    .getInstance()
                    .hasChessInVerticalLine(e.getPlayerIndex())
                    ? ((s = this.getInVerticalLineDicePoint(e, n, l)),
                      cc.director.emit(
                        a.GameEvent.Refresh_Player_Luck_Info,
                        p,
                        l,
                        t,
                        -2,
                        0
                      ))
                    : g.isCan && c.default.getInstance().getBarrierStatus(p)
                    ? ((s =
                        i.default.getRandomNum(1, 100) <= 85
                          ? g.dicePoint
                          : i.default.getRandomNum(1, 6)),
                      cc.director.emit(
                        a.GameEvent.Refresh_Player_Luck_Info,
                        p,
                        l,
                        t,
                        -2,
                        0
                      ))
                    : ((s =
                        1 == f
                          ? this.getNormalrandom(1.5, e)
                          : 2 == f
                          ? this.getNormalrandom(1.4, e)
                          : 3 == f
                          ? this.getNormalrandom(1.3, e)
                          : this.getNormalrandom(l, e)),
                      cc.director.emit(
                        a.GameEvent.Refresh_Player_Luck_Info,
                        p,
                        l,
                        t,
                        -2,
                        0
                      ));
                }
                return (
                  cc.log(
                    "LuckManager::getDicePoints,\u5f53\u524d\u6447\u5230\u7684\u70b9\u6570:" +
                      s
                  ),
                  s
                );
              }),
              (e.prototype.getNormalrandom = function (e, t) {
                var n = 0;
                this.playChase(t) && (n = 0.1);
                var o = Math.ceil(30 * e),
                  a =
                    (Math.ceil((0.3 + n) * e * 100),
                    Math.ceil((0.7 - 0.3 - n) * e * 100)),
                  r = i.default.getRandomNum(1, 100 * e);
                return r <= a
                  ? i.default.getRandomNum(1, 3)
                  : r > a && r <= o + a
                  ? i.default.getRandomNum(4, 5)
                  : 6;
              }),
              (e.prototype.playChase = function (e) {
                var t = !1;
                if (
                  u.default.getInstance().getRoomMode() == a.GameRoomMode.Quick
                ) {
                  for (
                    var n = r.default
                        .getInstance()
                        .getPlayerAllChess(e.getPlayerIndex()),
                      o = !0,
                      i = 0;
                    i < n.length;
                    i++
                  )
                    if (n[i].getCurrentPosIndex() > 25) {
                      o = !1;
                      break;
                    }
                  o && (t = this.isHaveEnemy(e));
                } else
                  u.default.getInstance().getRoomMode() ==
                    a.GameRoomMode.Classic && (t = this.isHaveEnemy(e));
                return t;
              }),
              (e.prototype.isHaveEnemy = function (e) {
                for (
                  var t = !1,
                    n = r.default
                      .getInstance()
                      .getPlayerAllChess(e.getPlayerIndex()),
                    o = 12;
                  o >= 1;
                  o--
                )
                  if (
                    l.default.getInstance().getCanEateOtherChess(n, o).length >
                    0
                  ) {
                    t = !0;
                    break;
                  }
                return t;
              }),
              (e.prototype.getInVerticalLineDicePoint = function (e, t, n) {
                var a = d.default.getInstance().getGameTotalRounds(),
                  s = 1,
                  c = r.default.getInstance().getEndPos(e.getPlayerIndex());
                if (1 == a)
                  c <= 5 && this._canEnterEndCount > 0
                    ? ((s = c), this._canEnterEndCount--)
                    : (s = this.getDefaultDicePoints());
                else if (2 == a)
                  c <= 5 && this._canEnterEndCount > 0
                    ? ((l = this.getProbability(0.9, c)) > o.DICE_MAX_POINTS ||
                        l == c) &&
                      ((s = c), this._canEnterEndCount--)
                    : (s = this.getDefaultDicePoints());
                else if (3 == a) {
                  var l;
                  c <= 5 && this._canEnterEndCount > 0
                    ? ((l = this.getProbability(0.8, c)) > o.DICE_MAX_POINTS ||
                        l == c) &&
                      ((s = c), this._canEnterEndCount--)
                    : (s = this.getDefaultDicePoints());
                } else if (this._canEnterEndCount > 0) {
                  var u = (t * n) / this._gameDifficultyJson.sixPointsDivide;
                  (s = i.default.getDicePointsByProbability(c, u)) == c &&
                    this._canEnterEndCount--;
                } else s = this.getDefaultDicePoints();
                return (
                  i.default.getRandomNum(1, 100) <= 50 &&
                    (s = this.getDefaultDicePoints()),
                  s
                );
              }),
              (e.prototype.getProbability = function (e, t) {
                var n = Math.ceil(
                    o.DICE_MAX_POINTS + o.DICE_MAX_POINTS * e * 10
                  ),
                  a = i.default.getRandomNum(1, n);
                return t == a || a > o.DICE_MAX_POINTS ? t : a;
              }),
              (e.prototype.getCanEateOtherChess = function (e, t) {
                for (
                  var n = e.getPlayerIndex(),
                    o = r.default.getInstance().getPlayerAllChess(n),
                    a = 1,
                    s = 0,
                    c = [],
                    u = d.default.getInstance().getGameTotalRounds(),
                    p = 6;
                  p >= 1;
                  p--
                )
                  if (
                    (c = l.default.getInstance().getCanEateOtherChess(o, p))
                      .length > 0
                  ) {
                    s = p;
                    break;
                  }
                if (0 != s)
                  if (1 == u) a = s;
                  else if (2 == u) a = this.getProbability(0.9, s);
                  else if (3 == u) a = this.getProbability(0.8, s);
                  else {
                    var f = 0.3 * t;
                    a = i.default.getDicePointsByProbability(s, f);
                  }
                var h = { isCan: !1, dicePoint: 1 };
                return (h.isCan = c.length > 0), (h.dicePoint = a), h;
              }),
              (e.prototype.getLevelDiff = function () {
                var e = d.default.getInstance().getMyselfUserInfo().getLevel(),
                  t = s.default.getInstance().getTools().getLeveDifficulty();
                for (var n in t.infos)
                  if (t.infos[n].level == e) return t.infos[n];
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = p), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Utils/Utils": "Utils",
        "./ChessManager": "ChessManager",
        "./GameDataManager": "GameDataManager",
        "./MapGridManager": "MapGridManager",
        "./RobotManager": "RobotManager",
        "./RoomInfoManager": "RoomInfoManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    MapGridManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "1c8b3/ExLRIgL7wsXXSNVix", "MapGridManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Utils/Utils"),
          i = e("./GameDataManager"),
          r = (function () {
            function e() {
              (this._mapGrids = []),
                (this._barrierStatus = [!0, !0, !0, !0]),
                (this._rocketGrids = []);
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.addMapGrid = function (e, t, n, o, a, i) {
                e.setGridInfo(t, n, o, a, i), this._mapGrids.push(e);
              }),
              (e.prototype.getMapGrid = function (e) {
                return this._mapGrids[e];
              }),
              (e.prototype.getPlayerPathInfo = function (e) {
                return i.default.getInstance().getTools().getMapInfoJson()
                  .paths[e];
              }),
              (e.prototype.getWalkPathMapGrids = function (e) {
                for (var t = [], n = 0; n < e.length; n++) {
                  var o = e[n];
                  if (
                    (t.push(this._mapGrids[o]),
                    this._mapGrids[o].hasRoadblock())
                  )
                    break;
                }
                return t;
              }),
              (e.prototype.setBarrierStatus = function (e, t) {
                this._barrierStatus[e] = t;
              }),
              (e.prototype.getBarrierStatus = function (e) {
                return this._barrierStatus[e];
              }),
              (e.prototype.isSafeGrid = function (e) {
                for (
                  var t = i.default.getInstance().getTools().getMapInfoJson(),
                    n = 0;
                  n < t.safeGrids.length;
                  n++
                )
                  if (e == t.safeGrids[n]) return !0;
                return !1;
              }),
              (e.prototype.getSafeGridIndexs = function () {
                return i.default.getInstance().getTools().getMapInfoJson()
                  .safeGrids;
              }),
              (e.prototype.isBarrierGrid = function (e) {
                for (
                  var t = i.default.getInstance().getTools().getMapInfoJson(),
                    n = 0;
                  n < t.barrierGrids.length;
                  n++
                )
                  if (e == t.barrierGrids[n]) return !0;
                return !1;
              }),
              (e.prototype.isIndicationGrid = function (e) {
                for (
                  var t = i.default.getInstance().getTools().getMapInfoJson(),
                    n = 0;
                  n < t.indicationGrids.length;
                  n++
                )
                  if (e == t.indicationGrids[n]) return n;
                return o.ARRAY_ELE_NOT_EXIST;
              }),
              (e.prototype.isColorGrid = function (e) {
                for (
                  var t = i.default.getInstance().getTools().getMapInfoJson(),
                    n = 0;
                  n < t.colorGrids.length;
                  n++
                )
                  for (var a = t.colorGrids[n], r = 0; r < a.length; r++)
                    if (e == a[r]) return n;
                return o.ARRAY_ELE_NOT_EXIST;
              }),
              (e.prototype.setRocketGrids = function () {
                var e = i.default.getInstance().getTools().getMapInfoJson();
                this._rocketGrids = a.default.getRandomArrayElements(
                  e.rocketGrids,
                  3
                );
              }),
              (e.prototype.isRocketGrid = function (e) {
                for (var t = 0; t < this._rocketGrids.length; t++)
                  if (e == this._rocketGrids[t]) return !0;
                return !1;
              }),
              (e.prototype.isInNormalLine = function (e) {
                return (
                  this.getPlayerPathInfo(0).normal.indexOf(e) !=
                  o.ARRAY_ELE_NOT_EXIST
                );
              }),
              (e.prototype.getVerticalLine = function (e) {
                var t = this.getPlayerPathInfo(e),
                  n = t.terminal.length - 1,
                  o = n - 5;
                return t.terminal.slice(o, n);
              }),
              (e.prototype.getAllMapGrid = function () {
                return this._mapGrids;
              }),
              (e.prototype.clearData = function () {
                (this._mapGrids = []), (this._rocketGrids = []);
                for (var e = 0; e < this._barrierStatus.length; e++)
                  this._barrierStatus[e] = !0;
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = r), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Utils/Utils": "Utils",
        "./GameDataManager": "GameDataManager",
      },
    ],
    MapGrid: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "45989zWjktIeKF6TgZDgSP1", "MapGrid");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/ChessManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Manager/MapGridManager"),
          p = e("../Framework/Manager/RoomInfoManager"),
          f = e("../Framework/Manager/ShopDataManager"),
          h = e("../Framework/Manager/UserInfoManager"),
          g = e("../Framework/Utils/Utils"),
          m = cc._decorator,
          _ = m.ccclass,
          y = m.property,
          v = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprGrid = null),
                (t.sprBarrierV = null),
                (t.sprBarrierH = null),
                (t.nodeBarrier = null),
                (t.sprSafeFlag = null),
                (t.sprIndication = null),
                (t.spfIndications = []),
                (t.spfGridColors = []),
                (t.buttonClickGrid = null),
                (t.sprGreenCircle = null),
                (t.labGridIndex = null),
                (t.node_grid = null),
                (t.spr_item = null),
                (t.sprItemList = []),
                (t.anim_bomb = null),
                (t._gridIndex = 0),
                (t._isSafe = !1),
                (t._chessArray = []),
                (t._isRocket = !1),
                (t._hasBomb = !1),
                (t._spfIndications = []),
                (t._spfGridColors = []),
                (t._colorList = ["lan", "hong", "lv", "huang"]),
                (t._isSprIndication = !1),
                (t._isHaveChess = !1),
                (t._roadblock = !1),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  (this.labGridIndex.node.active = !1),
                  this.updateInfo();
                var e = p.default.getInstance().getGameMode();
                this.spr_item.spriteFrame =
                  e == c.GameMode.BombItem
                    ? this.sprItemList[0]
                    : this.sprItemList[1];
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.ShowBombHelpTip,
                  this.ShowBombHelpTip,
                  this
                ),
                  this.registerEvent(c.GameEvent.ShowBomb, this.showBomb, this);
              }),
              (t.prototype.updateInfo = function () {
                var e = this,
                  t = this.sprBarrierV.getComponent(cc.Sprite),
                  n = this.sprBarrierH.getComponent(cc.Sprite),
                  o = f.default.getInstance().getSelectBoard(),
                  a = s.SKIN_PICTURE_PATH + o + "_img_barrier";
                this.loadRes(a, cc.SpriteFrame, function (e) {
                  (t.spriteFrame = e), (n.spriteFrame = e);
                });
                for (var i = 0; i < this._colorList.length; i++) {
                  var r =
                    s.SKIN_PICTURE_PATH +
                    o +
                    "_img_sanjiao_" +
                    this._colorList[i];
                  this.loadRes(r, cc.SpriteFrame, function (t) {
                    e._spfIndications.push(t);
                  });
                  var c =
                    s.SKIN_PICTURE_PATH + o + "_img_grid_" + this._colorList[i];
                  this.loadRes(c, cc.SpriteFrame, function (t) {
                    e._spfGridColors.push(t);
                  });
                }
                var l = this.sprSafeFlag.getComponent(cc.Sprite),
                  u = s.SKIN_PICTURE_PATH + o + "_img_wujiaoxing";
                this.loadRes(u, cc.SpriteFrame, function (e) {
                  l.spriteFrame = e;
                });
              }),
              (t.prototype.getSpfIndicationsRes = function (e, t) {
                var n = f.default.getInstance().getSelectBoard(),
                  o =
                    s.SKIN_PICTURE_PATH +
                    n +
                    "_img_sanjiao_" +
                    this._colorList[t];
                this.loadRes(o, cc.SpriteFrame, function (t) {
                  e.spriteFrame = t;
                });
              }),
              (t.prototype.setBarrierRotation = function (e) {
                52 == e
                  ? ((this.sprBarrierH.active = !0),
                    (this.sprBarrierV.active = !1))
                  : 58 == e
                  ? ((this.sprBarrierH.active = !1),
                    (this.sprBarrierV.active = !0))
                  : 64 == e
                  ? ((this.sprBarrierH.active = !0),
                    (this.sprBarrierV.active = !1))
                  : 70 == e
                  ? ((this.sprBarrierH.active = !1),
                    (this.sprBarrierV.active = !0))
                  : ((this.sprBarrierH.active = !0),
                    (this.sprBarrierV.active = !1));
              }),
              (t.prototype.setGridInfo = function (e, t, n, o, a) {
                if (
                  ((this._gridIndex = e),
                  (this.labGridIndex.string = "" + e),
                  (this._isSafe = t),
                  null != a
                    ? ((this.sprSafeFlag.active = !1), this.setGridColor(a))
                    : (this.sprSafeFlag.active = t),
                  (this.sprBarrierH.active = n),
                  (this.sprBarrierV.active = n),
                  n && this.setBarrierRotation(e),
                  o == s.ARRAY_ELE_NOT_EXIST)
                )
                  this.sprIndication.node.active = !1;
                else {
                  this.sprIndication.node.active = !0;
                  var i = l.default.getInstance().getPlayerChessColor(o),
                    r = u.default.getInstance().getTriangleRotation(o, i);
                  (this.sprIndication.node.rotation = r),
                    this.getSpfIndicationsRes(this.sprIndication, i);
                }
                this._isRocket = d.default.getInstance().isRocketGrid(e);
              }),
              (t.prototype.getGridIndex = function () {
                return this._gridIndex;
              }),
              (t.prototype.hideBarrier = function () {
                this.nodeBarrier.active = !1;
              }),
              (t.prototype.disappearBarrier = function () {
                this.nodeBarrier.runAction(
                  cc.sequence(
                    cc.spawn(
                      cc.scaleTo(2, 5),
                      cc.rotateBy(2, 360),
                      cc.fadeOut(2)
                    ),
                    cc.hide()
                  )
                );
              }),
              (t.prototype.setGridColor = function () {}),
              (t.prototype.isSafe = function () {
                return this._isSafe;
              }),
              (t.prototype.isRocket = function () {
                return this._isRocket;
              }),
              (t.prototype.hasBomb = function () {
                return this._hasBomb;
              }),
              (t.prototype.getIsHaveChess = function () {
                return this._isHaveChess;
              }),
              (t.prototype.hasRoadblock = function () {
                return this._roadblock;
              }),
              (t.prototype.setRoadblock = function (e) {
                (this._roadblock = e), (this.spr_item.node.active = e);
              }),
              (t.prototype.playBombEff = function (e) {
                (this.anim_bomb.node.active = !0),
                  this.anim_bomb.play(),
                  this.anim_bomb.on("finished", e);
              }),
              (t.prototype.playroadblock = function (e) {
                this.setRoadblock(!1), e && e();
              }),
              (t.prototype.setBomb = function (e) {
                (this._hasBomb = e), (this.spr_item.node.active = e);
              }),
              (t.prototype.getBombWorldPosition = function () {
                return g.default.getWorldPosition(this.node);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.checkChessExist = function (e) {
                for (var t = 0; t < this._chessArray.length; t++)
                  if (this._chessArray[t] == e) return !0;
                return !1;
              }),
              (t.prototype.adjustChessPosition = function () {
                if (this._chessArray.length > 0) {
                  var e = this.node;
                  if (1 == this._chessArray.length)
                    this._chessArray[0].setOriginalSize(),
                      (this._chessArray[0].node.x = e.x);
                  else {
                    for (var t = 0; t < this._chessArray.length; t++)
                      this._chessArray[t].setSmallerSize();
                    if (this._chessArray.length % 2 != 0) {
                      var n = Math.floor(this._chessArray.length / 2),
                        o = this._chessArray[n];
                      for (
                        o.node.x = e.x, t = 0;
                        t < this._chessArray.length;
                        t++
                      )
                        if (t != n)
                          if (t < n) {
                            var a = o.node.x - 10 * (n - t);
                            this._chessArray[t].node.x = a;
                          } else
                            (a = o.node.x + 10 * (t - n)),
                              (this._chessArray[t].node.x = a);
                    } else {
                      var i = e.x,
                        r = this._chessArray.length / 2,
                        s = i;
                      for (t = r - 1; t >= 0; t--)
                        (s -= t == r - 1 ? 5 : 10),
                          (this._chessArray[t].node.x = s);
                      var c = i;
                      for (t = r; t < this._chessArray.length; t++)
                        (c += t == r ? 5 : 10),
                          (this._chessArray[t].node.x = c);
                    }
                  }
                }
              }),
              (t.prototype.enterGrid = function (e) {
                this.checkChessExist(e)
                  ? cc.log("Chess::enterGrid error, chess is exist!")
                  : (this._chessArray.push(e), this.adjustChessPosition());
              }),
              (t.prototype.leaveGrid = function (e) {
                for (var t = 0; t < this._chessArray.length; t++)
                  if (this._chessArray[t] == e) {
                    this._chessArray.splice(t, 1);
                    break;
                  }
                this.adjustChessPosition();
              }),
              (t.prototype.getAllChess = function () {
                return this._chessArray;
              }),
              (t.prototype.getBeEatenChess = function (e) {
                var t = null;
                return (
                  1 == this._chessArray.length &&
                    this._chessArray[0].getOwnerPlayerIndex() !=
                      e.getOwnerPlayerIndex() &&
                    (t = this._chessArray[0]),
                  t
                );
              }),
              (t.prototype.isTouchPointInGrid = function (e) {
                var t = this.node.getBoundingBox(),
                  n = this.node.parent.convertToNodeSpaceAR(e);
                return t.contains(n);
              }),
              (t.prototype.getMyselfChess = function () {
                for (var e = [], t = 0; t < this._chessArray.length; t++)
                  this._chessArray[t].isMyselfChess() &&
                    e.push(this._chessArray[t]);
                return e;
              }),
              (t.prototype.onClickGrid = function () {
                this.disableClick(), this.getMyselfChess()[0].onClickChess();
              }),
              (t.prototype.disableClick = function () {
                this.buttonClickGrid.interactable = !1;
              }),
              (t.prototype.enableClick = function () {
                this.buttonClickGrid.interactable = !0;
              }),
              (t.prototype.isEmptyGrid = function () {
                return !(
                  this.isSafe() ||
                  this.isRocket() ||
                  this.hasBomb() ||
                  0 != this.getAllChess().length
                );
              }),
              (t.prototype.playGreenCircleAnim = function () {
                this.sprGreenCircle.stopAllActions(),
                  (this.sprGreenCircle.active = !0),
                  (this.sprGreenCircle.scale = 0.9),
                  this.sprGreenCircle.runAction(
                    cc.sequence(
                      cc.show(),
                      cc.delayTime(0.2),
                      cc.scaleTo(0.3, 0.5),
                      cc.hide()
                    )
                  );
              }),
              (t.prototype.isInNormalLine = function () {
                return d.default.getInstance().isInNormalLine(this._gridIndex);
              }),
              (t.prototype.ShowBombHelpTip = function (e) {
                for (
                  var t = u.default.getInstance().getTools().getMapInfoJson(),
                    n = [],
                    o = 0;
                  o < t.colorGrids.length;
                  o++
                )
                  for (var a = t.colorGrids[o], i = 0; i < a.length; i++)
                    n.push(a[i]);
                this._isSafe ||
                this._hasBomb ||
                this._isSprIndication ||
                this._isHaveChess
                  ? (this.node_grid.active = !1)
                  : -1 == n.indexOf(this._gridIndex) &&
                    ((this.node_grid.active = e), (this.node_grid.zIndex = 99));
              }),
              (t.prototype.showBomb = function (e) {
                var t = p.default.getInstance().getGameMode();
                this._gridIndex == e &&
                  0 == this._hasBomb &&
                  57 != this._gridIndex &&
                  63 != this._gridIndex &&
                  69 != this._gridIndex &&
                  75 != this._gridIndex &&
                  ((this.spr_item.node.active = !0),
                  t == c.GameMode.BombItem
                    ? (this._hasBomb = !0)
                    : t == c.GameMode.Roadblock && (this._roadblock = !0)),
                  this._gridIndex == e &&
                    cc.director.emit(c.GameEvent.ShowBombHelpTip, !1);
              }),
              (t.prototype.onBtnBombGridClick = function () {
                var e = h.default.getInstance().getMyselfUserInfo();
                u.default.getInstance().setBombInfo(e.getPlayerIndex()),
                  cc.director.emit(c.GameEvent.ShowBomb, this._gridIndex),
                  cc.director.emit(c.GameEvent.ShowBombHelpTip, !1),
                  (u.default.getInstance().canUseBomb = !1);
              }),
              i([y(cc.Sprite)], t.prototype, "sprGrid", void 0),
              i([y(cc.Node)], t.prototype, "sprBarrierV", void 0),
              i([y(cc.Node)], t.prototype, "sprBarrierH", void 0),
              i([y(cc.Node)], t.prototype, "nodeBarrier", void 0),
              i([y(cc.Node)], t.prototype, "sprSafeFlag", void 0),
              i([y(cc.Sprite)], t.prototype, "sprIndication", void 0),
              i([y(cc.SpriteFrame)], t.prototype, "spfIndications", void 0),
              i([y(cc.SpriteFrame)], t.prototype, "spfGridColors", void 0),
              i([y(cc.Button)], t.prototype, "buttonClickGrid", void 0),
              i([y(cc.Node)], t.prototype, "sprGreenCircle", void 0),
              i([y(cc.Label)], t.prototype, "labGridIndex", void 0),
              i([y(cc.Node)], t.prototype, "node_grid", void 0),
              i([y(cc.Sprite)], t.prototype, "spr_item", void 0),
              i([y(cc.SpriteFrame)], t.prototype, "sprItemList", void 0),
              i([y(cc.Animation)], t.prototype, "anim_bomb", void 0),
              i([_], t)
            );
          })(r.default);
        (n.default = v), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/ChessManager": "ChessManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/MapGridManager": "MapGridManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/ShopDataManager": "ShopDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    MatchPlayerView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "32912szWEJDu5Rfk+yvQmmj", "MatchPlayerView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/GameDataManager"),
          p = e("../Framework/Manager/RoomInfoManager"),
          f = e("../Framework/Manager/UserInfoManager"),
          h = e("../Framework/Utils/Utils"),
          g = e("./TurnHeadPhotoAnim"),
          m = e("../Framework/Native/NativeBridge"),
          _ = e("../Framework/Manager/AtlasResManager"),
          y = cc._decorator,
          v = y.ccclass,
          I = y.property,
          C = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprMyHeadPhoto = null),
                (t.labMyNickName = null),
                (t.labCD = null),
                (t.nodePlayers = []),
                (t._cdSecond = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                h.default.localStr(this.node),
                  m.default.closeBanner(),
                  this.setMyHeadPhoto(),
                  this.setMyNickName(),
                  this.startCDTimer(),
                  this.matchOtherPlayers(),
                  m.default.nativeLog("\u5f00\u59cb\u8c03\u6574\u573a\u666f"),
                  _.default.getInstance().loadGamePrefab(),
                  p.default.getInstance().setEntryGold(500),
                  p.default.getInstance().caculatePlayerWinGold(),
                  p.default.getInstance().setChessColor(c.ChessColor.Blue),
                  p.default.getInstance().setPlayerCount(4),
                  p.default.getInstance().setRoomMode(c.GameRoomMode.Quick),
                  p.default.getInstance().setGameMode(c.GameMode.Online),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.onlineGameMatchShow,
                    });
              }),
              (t.prototype.setMyHeadPhoto = function () {
                var e = this,
                  t = f.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getHeadPhotoIdx();
                this.loadRes(
                  s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + t,
                  cc.SpriteFrame,
                  function (t) {
                    e.sprMyHeadPhoto.spriteFrame = t;
                  }
                );
              }),
              (t.prototype.setMyNickName = function () {
                this.labMyNickName.string = f.default
                  .getInstance()
                  .getMyselfUserInfo()
                  .getNickName();
              }),
              (t.prototype.matchOtherPlayers = function () {
                var e = this;
                f.default.getInstance().generateGameUser();
                for (
                  var t = f.default.getInstance().getOhterUser(),
                    n = p.default.getInstance().getPlayerCount(),
                    o = 0,
                    a = function (a) {
                      i.loadRes(
                        s.HALL_PREFAB_PATH + "TurnHeadPhotoAnim",
                        cc.Prefab,
                        function (i) {
                          var r = null,
                            s = cc.instantiate(i),
                            l = s.getComponent(g.default);
                          n == c.PlayerCount.Two
                            ? ((s.parent = e.nodePlayers[1]),
                              (r =
                                e.nodePlayers[1].getChildByName("nodeSaoMiao")))
                            : ((s.parent = e.nodePlayers[a]),
                              (r =
                                e.nodePlayers[a].getChildByName(
                                  "nodeSaoMiao"
                                ))),
                            (r.zIndex = 10),
                            l.setInfo(
                              t[a].getNickName(),
                              t[a].getHeadPhotoIdx()
                            ),
                            l.startTurn(function () {
                              (r.active = !1),
                                (o += 1) == t.length && e.matchOver();
                            });
                        }
                      );
                    },
                    i = this,
                    r = 0;
                  r < t.length;
                  r++
                )
                  a(r);
              }),
              (t.prototype.matchOver = function () {
                this.closeCDTimer(),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.onlineGameMatchResult,
                    }),
                  this.scheduleOnce(function () {
                    l.default.getInstance().stopAllAudio(),
                      d.default.getInstance().getTools().getSkinInfo(),
                      d.default.getInstance().getGameType() ==
                        c.GameType.Ludo && cc.director.loadScene("Game_grass");
                  }, 0.01),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.MatchResult,
                      result: !0,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.MatchResult,
                      actionName: c.BuriedPointSecondKey.result,
                      value: 1,
                    });
              }),
              (t.prototype.start = function () {}),
              (t.prototype.onEnable = function () {}),
              (t.prototype.startCDTimer = function () {
                (this._cdSecond = 15),
                  (this.labCD.string = "00:" + this._cdSecond),
                  this.schedule(this.cdTimer, 1);
              }),
              (t.prototype.cdTimer = function () {
                (this._cdSecond -= 1),
                  this._cdSecond <= 0
                    ? this.closeCDTimer()
                    : (this.labCD.string = "00:" + this._cdSecond);
              }),
              (t.prototype.closeCDTimer = function () {
                this.unschedule(this.cdTimer), (this._cdSecond = 0);
              }),
              i([I(cc.Sprite)], t.prototype, "sprMyHeadPhoto", void 0),
              i([I(cc.Label)], t.prototype, "labMyNickName", void 0),
              i([I(cc.Label)], t.prototype, "labCD", void 0),
              i([I(cc.Node)], t.prototype, "nodePlayers", void 0),
              i([v], t)
            );
          })(r.default);
        (n.default = C), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AtlasResManager": "AtlasResManager",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "./TurnHeadPhotoAnim": "TurnHeadPhotoAnim",
      },
    ],
    ModifyCountryView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "0a47d0t+utESarRJijNCAu+", "ModifyCountryView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Utils/Utils"),
          p = e("../Login/CountryItem"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprCountry = null),
                (t.labCountryName = null),
                (t.countryContentNode = null),
                (t.countryItemPrefab = null),
                (t._selectCountryCode = ""),
                (t._callBack = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                d.default.localStr(this.node), this.registerAllEvents();
                var e = u.default.getInstance().getMyselfUserInfo();
                (this._selectCountryCode = e.getCountryCode()),
                  this.setCountryUI(e.getCountryName()),
                  this.initCountries();
              }),
              (t.prototype.setCallBack = function (e) {
                this._callBack = e;
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  s.GameEvent.User_Info_Select_Country,
                  this.onSelectCountry,
                  this
                );
              }),
              (t.prototype.initCountries = function () {
                for (
                  var e = u.default.getInstance().getMyselfUserInfo(),
                    t = l.default
                      .getInstance()
                      .getTools()
                      .getCountryJson().countries,
                    n = 0;
                  n < t.length;
                  n++
                ) {
                  var o = t[n].countryCode,
                    a = t[n].countryName,
                    i = e.getCountryCode() == o,
                    r = cc.instantiate(this.countryItemPrefab);
                  (r.x = 13),
                    (r.parent = this.countryContentNode),
                    r.getComponent(p.default).setInfo(o, a, i);
                }
              }),
              (t.prototype.onSelectCountry = function (e, t) {
                (this._selectCountryCode = e), this.setCountryUI(t);
              }),
              (t.prototype.setCountryUI = function (e) {
                var t = this;
                if ("" == this._selectCountryCode)
                  (this.sprCountry.node.active = !1),
                    (this.labCountryName.node.active = !1);
                else {
                  (this.sprCountry.node.active = !0),
                    (this.labCountryName.node.active = !0);
                  var n = "country_icon_" + this._selectCountryCode;
                  this.loadRes(n, cc.SpriteFrame, function (e) {
                    t.sprCountry.spriteFrame = e;
                  }),
                    (this.labCountryName.string = e);
                }
              }),
              (t.prototype.onClickSure = function () {
                this._callBack && this._callBack(),
                  c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                  u.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .setCountryCode(this._selectCountryCode),
                  this.onClose();
              }),
              (t.prototype.onCloseClick = function () {
                this._callBack && this._callBack(), this.onClose();
              }),
              i([g(cc.Sprite)], t.prototype, "sprCountry", void 0),
              i([g(cc.Label)], t.prototype, "labCountryName", void 0),
              i([g(cc.Node)], t.prototype, "countryContentNode", void 0),
              i([g(cc.Prefab)], t.prototype, "countryItemPrefab", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
        "../Login/CountryItem": "CountryItem",
      },
    ],
    ModifyHeadPhotoView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "7f298493BZHg6FHMGPE0sj2", "ModifyHeadPhotoView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Utils/Utils"),
          p = e("./HeadPhotoItem"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.headPhotoContentNode = null),
                (t.headPhotoItemPrefab = null),
                (t._curSelectHeadPhotoIdx = 0),
                (t._callBack = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                d.default.localStr(this.node),
                  this.registerAllEvents(),
                  (this._curSelectHeadPhotoIdx = u.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getHeadPhotoIdx()),
                  this.initHeadPhotos();
              }),
              (t.prototype.setCallBack = function (e) {
                this._callBack = e;
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.User_Info_Select_HeadPhoto,
                  this.onSelectHeadPhotoIdx,
                  this
                );
              }),
              (t.prototype.initHeadPhotos = function () {
                for (var e = [], t = 1; t <= s.PLAYER_HEAD_PHOTO_COUNT; t++)
                  e.push(t);
                var n = d.default.splitCountArray(e, 4);
                for (t = 0; t < n.length; t++) {
                  var o = n[t],
                    a = cc.instantiate(this.headPhotoItemPrefab);
                  (a.parent = this.headPhotoContentNode),
                    (a.x += 10),
                    a.getComponent(p.default).setInfo(o);
                }
              }),
              (t.prototype.onSelectHeadPhotoIdx = function (e) {
                this._curSelectHeadPhotoIdx = e;
              }),
              (t.prototype.onClickReplace = function () {
                this._callBack && this._callBack(),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  u.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .setHeadPhotoIdx(this._curSelectHeadPhotoIdx),
                  this.onClose();
              }),
              (t.prototype.onCloseClick = function () {
                this._callBack && this._callBack(), this.onClose();
              }),
              i([g(cc.Node)], t.prototype, "headPhotoContentNode", void 0),
              i([g(cc.Prefab)], t.prototype, "headPhotoItemPrefab", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
        "./HeadPhotoItem": "HeadPhotoItem",
      },
    ],
    NativeBridge: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "fd4b7duXURK76CMntPJxUz4", "NativeBridge"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("../Manager/BuriedPointManager"),
          r = e("../Manager/GameDataManager"),
          s = e("../Manager/GlobalTimerManager"),
          c = e("../Manager/RoomInfoManager"),
          l = e("../Manager/UserInfoManager"),
          u = e("../Utils/Utils"),
          d = (function () {
            function e() {}
            return (
              (e.init = function () {
                e.isInit ||
                  ((e.isInit = !0),
                  (window.NativeBridge = e),
                  e.initPay(),
                  (this.time = u.default.getCurTimeStamp()));
              }),
              (e.isAndroid = function () {
                return cc.sys.platform == cc.sys.ANDROID;
              }),
              (e.isNative = function () {
                return this.isAndroid();
              }),
              (e.isBrowser = function () {
                return cc.sys.isBrowser;
              }),
              (e.loadReward = function () {
                if (this.isAndroid()) {
                  var e = { type: this._curADType.split("_Insert")[0] };
                  console.log("\u65b0\u52a0\u7684loadReward:log"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "loadReward",
                      "(Ljava/lang/String;)V",
                      JSON.stringify(e)
                    ),
                    r.default
                      .getInstance()
                      .getTools()
                      .startAdLoading(function () {
                        r.default
                          .getInstance()
                          .getTools()
                          .showTips(
                            u.default.replaceStr(
                              "Ad failed to load,please try again later."
                            )
                          );
                      });
                }
              }),
              (e.isInsterScreenAD = function (e) {
                return e.indexOf("_Insert") != o.ARRAY_ELE_NOT_EXIST;
              }),
              (e.watchVideo = function (e, t) {
                if (
                  (void 0 === t && (t = "Default"),
                  (this._watchVideoFinishCallback = e),
                  (this._curADType = t),
                  this.isAndroid())
                )
                  this.isInsterScreenAD(t)
                    ? (console.log("InsterScreenAD"),
                      this._watchVideoFinishCallback &&
                        (this._watchVideoFinishCallback(),
                        (this._watchVideoFinishCallback = null)),
                      this.showInterstitial())
                    : this._curADType == a.ADType.Default
                    ? (console.log("ADType.Default"),
                      this.getRewardLoadType()
                        ? this.callWatchVideo()
                        : this._watchVideoFinishCallback &&
                          (this._watchVideoFinishCallback(),
                          (this._watchVideoFinishCallback = null)))
                    : this.getNetworkStatus() == a.NetworkStatus.No
                    ? (console.log("NetworkStatus.No"),
                      r.default
                        .getInstance()
                        .getTools()
                        .showTips(u.default.replaceStr("network_error")))
                    : this.getRewardLoadType()
                    ? (this.callWatchVideo(),
                      console.log(
                        "\u6709\u5e7f\u544a\u7f13\u5b58,\u5219\u76f4\u63a5\u770b\u5e7f\u544a"
                      ))
                    : (console.log(
                        "\u6ca1\u6709\u5e7f\u544a\u7f13\u5b58\uff0c\u9700\u8981loading"
                      ),
                      this.loadReward());
                else if (this.isBrowser()) {
                  var n = this._curADType.split("_Insert");
                  this.isInsterScreenAD(t)
                    ? (console.log("InsterScreenAD"),
                      this.showInterstitialAd(n[0]))
                    : this.showRewardAd(n[0]);
                } else this._watchVideoFinishCallback();
              }),
              (e.showRewardAd = function (e) {
                this._googleShowReward
                  ? (this._googleShowReward(),
                    console.log("\u6267\u884c_googleShowReward"),
                    (this._googleShowReward = null),
                    i.default
                      .getInstance()
                      .sendBuriedPointInfo({ event: e + "_YES" }))
                  : (r.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        u.default.replaceStr(
                          "Ad failed to load,please try again later."
                        )
                      ),
                    this.loadShowReward(e));
              }),
              (e.showTailAd = function () {
                window.adBreak({
                  type: "preroll",
                  adBreakDone: function (e) {
                    console.log(
                      "google adsense \u5f00\u5c4f\u663e\u793a\u5931\u8d25" + e
                    );
                  },
                });
              }),
              (e.showInterstitialAd = function (e) {
                o.BROWSER_ATHENA
                  ? (window.h5sdk &&
                      window.h5sdk.adBreak({
                        type: "start",
                        name: e,
                        beforeAd: function () {
                          console.log(
                            "google adsense \u5f00\u59cb\u663e\u793a\u63d2\u5c4f" +
                              e
                          );
                        },
                        afterAd: function () {
                          i.default
                            .getInstance()
                            .sendBuriedPointInfo({
                              event: "SHOW" + e + "_YES",
                            }),
                            console.log(
                              "google adsense \u63d2\u5c4f\u5b8c\u6210" + e
                            );
                        },
                        adBreakDone: function (t) {
                          i.default
                            .getInstance()
                            .sendBuriedPointInfo({ event: "SHOW" + e + "_NO" }),
                            console.log(
                              "google adsense \u63d2\u5c4f\u663e\u793a\u5931\u8d25" +
                                t.breakStatus +
                                "-------" +
                                e
                            );
                        },
                      }),
                    this._watchVideoFinishCallback &&
                      this._watchVideoFinishCallback())
                  : this._watchVideoFinishCallback();
              }),
              (e.loadShowReward = function (e) {
                var t = this;
                this._googleShowReward ||
                  (o.BROWSER_ATHENA
                    ? window.h5sdk &&
                      window.h5sdk.adBreak({
                        type: "reward",
                        name: e,
                        beforeAd: function () {
                          console.log(
                            "google adsense \u5f00\u59cb\u64ad\u653e" + e
                          );
                        },
                        afterAd: function () {
                          console.log("google adsense afterAd" + e);
                        },
                        beforeReward: function (t) {
                          console.log("load Reward AD Successful" + e),
                            t(),
                            i.default
                              .getInstance()
                              .sendBuriedPointInfo({
                                event: "Load" + e + "_YES",
                              });
                        },
                        adDismissed: function () {},
                        adViewed: function () {
                          (t._googleShowReward = null),
                            t._watchVideoFinishCallback &&
                              t._watchVideoFinishCallback(),
                            i.default
                              .getInstance()
                              .sendBuriedPointInfo({
                                event: "SHOW" + e + "_YES",
                              }),
                            console.log(
                              "google adsense \u7ed3\u675f\u64ad\u653e" + e
                            );
                        },
                        adBreakDone: function (t) {
                          i.default
                            .getInstance()
                            .sendBuriedPointInfo({ event: "Load" + e + "_NO" }),
                            cc.director.resume(),
                            console.log(
                              "google adsense \u6fc0\u52b1\u89c6\u9891\u663e\u793a\u5931\u8d25" +
                                t.breakStatus +
                                "-------" +
                                e
                            );
                        },
                      })
                    : this._watchVideoFinishCallback &&
                      this._watchVideoFinishCallback());
              }),
              (e.callWatchVideo = function () {
                var e = { type: this._curADType.split("_Insert")[0] };
                console.log("\u65b0\u52a0\u7684watchVideo:log"),
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "watchVideo",
                    "(Ljava/lang/String;)V",
                    JSON.stringify(e)
                  );
              }),
              (e.watchVideoCallback = function (e) {
                if (
                  (this.nativeLog("watchVideoCallback--jsonInfo:" + e),
                  e && "" != e)
                ) {
                  var t = JSON.parse(e);
                  0 == t.type
                    ? (this.nativeLog("\u5e7f\u544a\u89c2\u770b\u6210\u529f"),
                      this._watchVideoFinishCallback &&
                        (this._watchVideoFinishCallback(),
                        (this._watchVideoFinishCallback = null),
                        this._curADType != a.ADType.Default &&
                          s.default
                            .getInstance()
                            .startADRewardTimer(o.AD_REWARD_CD_TIME)))
                    : 1 == t.type
                    ? this.nativeLog("\u5e7f\u544a\u89c2\u770b\u4e2d\u65ad")
                    : 2 == t.type &&
                      this.nativeLog("\u5e7f\u544a\u89c2\u770b\u5931\u8d25");
                }
              }),
              (e.payInitCallback = function (e) {
                if (e && "" != e) {
                  this.nativeLog("payInitCallback--jsonInfo:" + e);
                  var t = JSON.parse(e);
                  r.default.getInstance().setPayInitSuccess(1 == t.type),
                    1 == t.type && l.default.getInstance().loadGoodsInfo();
                }
              }),
              (e.getDataCallback = function (e) {
                if (e && "" != e) {
                  this.nativeLog("getDataCallback--jsonInfo:" + e);
                  var t = JSON.parse(e);
                  t.key &&
                    this._getDataCallbackInfos[t.key] &&
                    (0, this._getDataCallbackInfos[t.key])(t.value);
                }
              }),
              (e.getNetworkStatus = function () {
                return this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "getNetworkStatus",
                      "()I"
                    )
                  : this.isBrowser()
                  ? this._netStatus
                  : void 0;
              }),
              (e.setNetWortStatus = function (e) {
                this._netStatus = e;
              }),
              (e.jumpToNetworkSettings = function () {
                this.isAndroid() &&
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "jumpToNetworkSettings",
                    "()V"
                  );
              }),
              (e.getData = function (e, t) {
                return (
                  t || (t = ""),
                  this.isAndroid()
                    ? jsb.reflection.callStaticMethod(
                        this._className,
                        "getData",
                        "(Ljava/lang/String;)Ljava/lang/String;",
                        e
                      ) || ""
                    : this.isBrowser()
                    ? cc.sys.localStorage.getItem(e) || ""
                    : void 0
                );
              }),
              (e.saveData = function (e, t) {
                this.nativeLog(
                  "rechargeCallback--saveData-----------------------:"
                ),
                  this.isAndroid()
                    ? jsb.reflection.callStaticMethod(
                        this._className,
                        "saveData",
                        "(Ljava/lang/String;Ljava/lang/String;)V",
                        e,
                        t
                      )
                    : this.isBrowser() && cc.sys.localStorage.setItem(e, t);
              }),
              (e.recharge = function (e, t) {
                (this._rechargeSuccessCallback = e),
                  this.isAndroid() &&
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "recharge",
                      "(Ljava/lang/String;)V",
                      t
                    );
              }),
              (e.vasRecharge = function (e, t) {
                (this._rechargeSuccessCallback = e),
                  this.isAndroid() &&
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "sendVasPay",
                      "(Ljava/lang/String;)V",
                      t
                    );
              }),
              (e.rechargeCallback = function (e) {
                e &&
                  "" != e &&
                  (this.nativeLog("rechargeCallback--jsonInfo:" + e),
                  1 == JSON.parse(e).type
                    ? this._rechargeSuccessCallback &&
                      (this._rechargeSuccessCallback(),
                      (this._rechargeSuccessCallback = null))
                    : r.default
                        .getInstance()
                        .getTools()
                        .showTips(u.default.replaceStr("store_paymentfailed")));
              }),
              (e.nativeLog = function (e, t) {
                this.isAndroid()
                  ? ((null != t && null != t) || (t = "***JSNativeBridge***"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "nativeLog",
                      "(Ljava/lang/String;Ljava/lang/String;)V",
                      t,
                      e
                    ))
                  : this.isBrowser() &&
                    cc.log("***********nativeLog****************, msg" + e);
              }),
              (e.addADBanner = function () {
                this.isAndroid() &&
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "addADBanner",
                    "()V"
                  );
              }),
              (e.showBanner = function () {
                this.isAndroid()
                  ? (console.log("\u663e\u793abanner\u5e7f\u544a"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "showBanner",
                      "()V"
                    ))
                  : this.isBrowser() && o.BROWSER_ATHENA && window.showBanner();
              }),
              (e.showBannerTop = function () {
                this.isAndroid() &&
                  (console.log("\u663e\u793abanner\u5e7f\u544a"),
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "showBannerTop",
                    "()V"
                  ));
              }),
              (e.closeBanner = function () {
                this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "closeBanner",
                      "()V"
                    )
                  : this.isBrowser() &&
                    o.BROWSER_ATHENA &&
                    window.closeBanner();
              }),
              (e.getLanguageStr = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "getLanguage",
                    "()Ljava/lang/String;"
                  );
                  return console.log("\u591a\u8bed\u8a00data: " + e), e;
                }
                return "1";
              }),
              (e.getGoodsInfo = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "GetPayInfo",
                    "()Ljava/lang/String;"
                  );
                  return this.nativeLog("getGoodsInfo:" + e), e;
                }
                return this.isBrowser(), "";
              }),
              (e.getVasPayInfo = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "GetVasPayInfo",
                    "()Ljava/lang/String;"
                  );
                  return this.nativeLog("getVasInfo:" + e), e;
                }
                return this.isBrowser(), "";
              }),
              (e.getGameVersion = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "getGameVersion",
                    "()Ljava/lang/String;"
                  );
                  return this.nativeLog("getGameVersion:" + e), e;
                }
              }),
              (e.getBarHeight = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "getStatusBarHeight",
                    "()Ljava/lang/String;"
                  );
                  return this.nativeLog("getStatusBarHeight:" + e), e;
                }
              }),
              (e.isGP = function () {
                if (this.isAndroid()) {
                  var e = jsb.reflection.callStaticMethod(
                    this._className,
                    "getAppMetaDataString",
                    "()Ljava/lang/String;"
                  );
                  return this.nativeLog("IS_gp:" + e), "GP" == e;
                }
                return this.isBrowser(), !1;
              }),
              (e.sendBuriedPointInfo = function (e) {
                this.isAndroid() &&
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "sendBuriedPointInfo",
                    "(Ljava/lang/String;)V",
                    e
                  );
              }),
              (e.initPay = function () {
                this.isAndroid() &&
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "initPay",
                    "()V"
                  );
              }),
              (e.getRewardLoadType = function () {
                return this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "getRewardLoadType",
                      "()Z"
                    )
                  : !!this.isBrowser() || void 0;
              }),
              (e.getIsInterstitialReady = function () {
                return this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "getIsInterstitialReady",
                      "()Z"
                    )
                  : !this.isBrowser() && void 0;
              }),
              (e.preloadReward = function () {}),
              (e.preInterstitialReady = function (e) {
                if (this.isAndroid() && 0 == this.getIsInterstitialReady()) {
                  var t = { type: e.split("_Insert")[0] };
                  console.log("\u65b0\u52a0\u7684LoadInterstitial:log"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "LoadInterstitial",
                      "(Ljava/lang/String;)V",
                      JSON.stringify(t)
                    );
                }
              }),
              (e.ADCacheCallback = function (e) {
                console.log("\u6536\u5230\u56de\u8c03\uff1a ADCacheCallback"),
                  e &&
                    "" != e &&
                    (this.nativeLog("ADCacheCallback--jsonInfo:" + e),
                    1 == JSON.parse(e).type
                      ? (this.callWatchVideo(),
                        cc.director.emit(a.GameEvent.AD_Cache_Success))
                      : cc.director.emit(a.GameEvent.AD_Cache_Fail));
              }),
              (e.getCountryCallback = function (e) {
                this.nativeLog("getCountryCallback--jsonInfo:" + e);
              }),
              (e.showInterstitial = function () {
                if (this.isAndroid()) {
                  var e = { type: this._curADType.split("_Insert")[0] };
                  console.log("\u65b0\u52a0\u7684showInterstitial\uff1alog"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "showInterstitial",
                      "(Ljava/lang/String;)V",
                      JSON.stringify(e)
                    );
                } else this.isBrowser();
              }),
              (e.showNoAdmobInterstitial = function (e) {
                if (this.isAndroid()) {
                  var t = { type: e.split("_Insert")[0] };
                  console.log("showNoAdmobInterstitial:log"),
                    jsb.reflection.callStaticMethod(
                      this._className,
                      "showNoAdmobInterstitial",
                      "(Ljava/lang/String;)V",
                      JSON.stringify(t)
                    );
                } else this.isBrowser();
              }),
              (e.getCloudControlConfig = function (e) {
                if (this.isAndroid()) {
                  var t = jsb.reflection.callStaticMethod(
                    this._className,
                    "getRemoteConfig",
                    "(Ljava/lang/String;)Ljava/lang/String;",
                    e
                  );
                  this.nativeLog(
                    "getCloudControlConfig, key:" + e + " data:" + t
                  );
                  try {
                    if ("" != t) return JSON.parse(t);
                  } catch (n) {
                    this.nativeLog(
                      "getCloudControlConfig, json\u89e3\u6790\u5931\u8d25, key:" +
                        e
                    );
                  }
                } else this.isBrowser();
              }),
              (e.addAHAActivityCount = function () {
                this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "addAHAActivityCount",
                      "()V"
                    )
                  : this.isBrowser();
              }),
              (e.openAHA = function () {
                if (this.isAndroid()) {
                  var e = r.default.getInstance().getTools().getGlobalJson()
                    .info[0].AHAUrl;
                  console.log("AHAUrl: " + e),
                    e &&
                      jsb.reflection.callStaticMethod(
                        this._className,
                        "openAHAActivity",
                        "(Ljava/lang/String;)V",
                        e
                      );
                } else this.isBrowser();
              }),
              (e.showAppluck = function () {
                this.isAndroid()
                  ? jsb.reflection.callStaticMethod(
                      this._className,
                      "ShowAppluck",
                      "()V"
                    )
                  : this.isBrowser();
              }),
              (e.hideAppluck = function () {
                this.isAndroid() &&
                  jsb.reflection.callStaticMethod(
                    this._className,
                    "hideInteractiveEntrance",
                    "()V"
                  );
              }),
              (e.activityPlayGame = function (t) {
                var n = this;
                this.nativeLog(
                  "H5\u9875\u9762\u8fd4\u56de\u6e38\u620f\uff0c\u8fdb\u5165\u5339\u914d\u754c\u9762+ " +
                    t
                ),
                  l.default.getInstance().getMyselfUserInfo().getGoldNum() >=
                  500
                    ? e.watchVideo(function () {
                        n.selectMaxGold(),
                          c.default
                            .getInstance()
                            .setGameMode(a.GameMode.Online),
                          c.default
                            .getInstance()
                            .setPlayerCount(a.PlayerCount.Four),
                          c.default
                            .getInstance()
                            .setRoomMode(a.GameRoomMode.Quick),
                          c.default.getInstance().caculatePlayerWinGold(),
                          r.default.getInstance().setFristEnterGame(!1),
                          cc.director.emit(a.GameEvent.Popup_Match_Player);
                      }, a.ADType.Activity)
                    : r.default
                        .getInstance()
                        .getTools()
                        .showTips("Not Enough Coins");
              }),
              (e.selectMaxGold = function () {
                for (
                  var e = r.default
                      .getInstance()
                      .getTools()
                      .getEntryCoinsJson(),
                    t = 0;
                  t < e.infos.length;
                  t++
                )
                  this._entryGoldArray.push(e.infos[t].coins);
                var n = l.default.getInstance().getMyselfUserInfo(),
                  o = 0,
                  a = this.getGoldArrayByLevel();
                for (t = a.length - 1; t >= 0; t--)
                  if (n.getGoldNum() >= a[t]) {
                    o = t;
                    break;
                  }
                c.default.getInstance().setEntryGold(a[o]);
              }),
              (e.getGoldArrayByLevel = function () {
                var e,
                  t = [],
                  n = l.default.getInstance().getMyselfUserInfo().getLevel();
                e =
                  n < 5
                    ? 1e4
                    : n >= 5 && n < 8
                    ? 5e4
                    : n >= 8 && n < 11
                    ? 1e5
                    : n >= 11 && n < 14
                    ? 5e5
                    : n >= 14 && n < 17
                    ? 1e6
                    : n >= 17 && n < 20
                    ? 5e6
                    : 1e7;
                for (var o = 0; o < this._entryGoldArray.length; o++)
                  this._entryGoldArray[o] <= e &&
                    t.push(this._entryGoldArray[o]);
                return t;
              }),
              (e.setUniqueID = function (e) {
                this._uniqueid = e;
              }),
              (e.getChainId = function () {
                if (o.ISAPPLET) return this.time + "_" + this._uniqueid;
              }),
              (e.addToHomeScreen = function (e) {
                window.addToHomeScreen(e);
              }),
              (e.downLoadLudo = function () {
                this.isBrowser() && o.BROWSER_ATHENA && window.downLoadLudo();
              }),
              (e.isInit = !1),
              (e._watchVideoFinishCallback = null),
              (e._rechargeSuccessCallback = null),
              (e._curADType = ""),
              (e._className = "org/cocos2dx/javascript/JSNativeBridge_GP"),
              (e._getDataCallbackInfos = {}),
              (e._netStatus = a.NetworkStatus.Normal),
              (e._entryGoldArray = []),
              (e._googleShowReward = null),
              (e._uniqueid = null),
              (e.time = null),
              e
            );
          })();
        (n.default = d), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Manager/BuriedPointManager": "BuriedPointManager",
        "../Manager/GameDataManager": "GameDataManager",
        "../Manager/GlobalTimerManager": "GlobalTimerManager",
        "../Manager/RoomInfoManager": "RoomInfoManager",
        "../Manager/UserInfoManager": "UserInfoManager",
        "../Utils/Utils": "Utils",
      },
    ],
    NetInterface: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "d9f8b+CV69FyKwnUdCjOtad", "NetInterface"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.DefStringProtocol = void 0);
        var o = (function () {
          function e() {}
          return (
            (e.prototype.getHeadlen = function () {
              return 0;
            }),
            (e.prototype.getHearbeat = function () {
              return "";
            }),
            (e.prototype.getPackageLen = function (e) {
              return e.toString().length;
            }),
            (e.prototype.checkPackage = function () {
              return !0;
            }),
            (e.prototype.getPackageId = function () {
              return 0;
            }),
            e
          );
        })();
        (n.DefStringProtocol = o), cc._RF.pop();
      },
      {},
    ],
    NetManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "d8cd5el6GBGTYTW+N8b8EuJ", "NetManager"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.NetManager = void 0);
        var o = (function () {
          function e() {
            this._channels = {};
          }
          return (
            (e.getInstance = function () {
              return (
                null == this._instance && (this._instance = new e()),
                this._instance
              );
            }),
            (e.prototype.setNetNode = function (e, t) {
              void 0 === t && (t = 0), (this._channels[t] = e);
            }),
            (e.prototype.removeNetNode = function (e) {
              delete this._channels[e];
            }),
            (e.prototype.connect = function (e, t) {
              return (
                void 0 === t && (t = 0),
                !!this._channels[t] && this._channels[t].connect(e)
              );
            }),
            (e.prototype.send = function (e, t, n) {
              void 0 === t && (t = !1), void 0 === n && (n = 0);
              var o = this._channels[n];
              return !!o && o.send(e, t);
            }),
            (e.prototype.request = function (e, t, n, o, a, i) {
              void 0 === o && (o = !0),
                void 0 === a && (a = !1),
                void 0 === i && (i = 0);
              var r = this._channels[i];
              r && r.request(e, t, n, o, a);
            }),
            (e.prototype.requestUnique = function (e, t, n, o, a, i) {
              void 0 === o && (o = !0),
                void 0 === a && (a = !1),
                void 0 === i && (i = 0);
              var r = this._channels[i];
              return !!r && r.requestUnique(e, t, n, o, a);
            }),
            (e.prototype.close = function (e, t, n) {
              if ((void 0 === n && (n = 0), this._channels[n]))
                return this._channels[n].closeSocket(e, t);
            }),
            (e._instance = null),
            e
          );
        })();
        (n.NetManager = o), cc._RF.pop();
      },
      {},
    ],
    NetNode: [
      function (e, t, n) {
        "use strict";
        var o, a;
        cc._RF.push(t, "57f0fB90kNBUJ98yyu+jxjx", "NetNode"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.NetNode = n.NetNodeState = n.NetTipsType = void 0),
          (function (e) {
            (e[(e.Connecting = 0)] = "Connecting"),
              (e[(e.ReConnecting = 1)] = "ReConnecting"),
              (e[(e.Requesting = 2)] = "Requesting");
          })((o = n.NetTipsType || (n.NetTipsType = {}))),
          (function (e) {
            (e[(e.Closed = 0)] = "Closed"),
              (e[(e.Connecting = 1)] = "Connecting"),
              (e[(e.Checking = 2)] = "Checking"),
              (e[(e.Working = 3)] = "Working");
          })((a = n.NetNodeState || (n.NetNodeState = {})));
        var i = (function () {
          function e() {
            (this._connectOptions = null),
              (this._autoReconnect = 0),
              (this._isSocketInit = !1),
              (this._isSocketOpen = !1),
              (this._state = a.Closed),
              (this._socket = null),
              (this._networkTips = null),
              (this._protocolHelper = null),
              (this._connectedCallback = null),
              (this._disconnectCallback = null),
              (this._callbackExecuter = null),
              (this._keepAliveTimer = null),
              (this._receiveMsgTimer = null),
              (this._reconnectTimer = null),
              (this._heartTime = 1e4),
              (this._receiveTime = 6e6),
              (this._reconnetTimeOut = 8e6),
              (this._requests = Array()),
              (this._listener = {});
          }
          return (
            (e.prototype.init = function (e, t, n, o) {
              void 0 === n && (n = null),
                void 0 === o && (o = null),
                console.log("NetNode init socket"),
                (this._socket = e),
                (this._protocolHelper = t),
                (this._networkTips = n),
                (this._callbackExecuter =
                  o ||
                  function (e, t) {
                    e.callback.call(e.target, 0, t);
                  });
            }),
            (e.prototype.connect = function (e) {
              return !(
                !this._socket ||
                this._state != a.Closed ||
                (this._isSocketInit || this.initSocket(),
                (this._state = a.Connecting),
                this._socket.connect(e)
                  ? (null == this._connectOptions &&
                      (this._autoReconnect = e.autoReconnect),
                    (this._connectOptions = e),
                    this.updateNetTips(o.Connecting, !0),
                    0)
                  : (this.updateNetTips(o.Connecting, !1), 1))
              );
            }),
            (e.prototype.initSocket = function () {
              var e = this;
              (this._socket.onConnected = function (t) {
                e.onConnected(t);
              }),
                (this._socket.onMessage = function (t) {
                  e.onMessage(t);
                }),
                (this._socket.onError = function (t) {
                  e.onError(t);
                }),
                (this._socket.onClosed = function (t) {
                  e.onClosed(t);
                }),
                (this._isSocketInit = !0);
            }),
            (e.prototype.updateNetTips = function (e, t) {
              this._networkTips &&
                (e == o.Requesting
                  ? this._networkTips.requestTips(t)
                  : e == o.Connecting
                  ? this._networkTips.connectTips(t)
                  : e == o.ReConnecting && this._networkTips.reconnectTips(t));
            }),
            (e.prototype.onConnected = function () {
              var e = this;
              console.log("NetNode onConnected!"),
                (this._isSocketOpen = !0),
                null !== this._connectedCallback
                  ? ((this._state = a.Checking),
                    this._connectedCallback(function () {
                      e.onChecked();
                    }))
                  : this.onChecked(),
                console.log("NetNode onConnected! state =" + this._state);
            }),
            (e.prototype.onChecked = function () {
              if (
                (console.log("NetNode onChecked!"),
                (this._state = a.Working),
                this.updateNetTips(o.Connecting, !1),
                this.updateNetTips(o.ReConnecting, !1),
                console.log(
                  "NetNode flush " + this._requests.length + " request"
                ),
                this._requests.length > 0)
              ) {
                for (var e = 0; e < this._requests.length; ) {
                  var t = this._requests[e];
                  this._socket.send(t.buffer),
                    null == t.rspObject || t.rspCmd <= 0
                      ? this._requests.splice(e, 1)
                      : ++e;
                }
                this.updateNetTips(o.Requesting, this.request.length > 0);
              }
            }),
            (e.prototype.onMessage = function (e) {
              if (this._protocolHelper.checkPackage(e)) {
                this.resetReceiveMsgTimer(), this.resetHearbeatTimer();
                var t = this._protocolHelper.getPackageId(e);
                if (
                  (console.log("NetNode onMessage rspCmd = " + t),
                  this._requests.length > 0)
                ) {
                  for (var n in this._requests) {
                    var a = this._requests[n];
                    if (a.rspCmd == t) {
                      console.log("NetNode execute request rspcmd " + t),
                        this._callbackExecuter(a.rspObject, e),
                        this._requests.splice(parseInt(n), 1);
                      break;
                    }
                  }
                  console.log(
                    "NetNode still has " +
                      this._requests.length +
                      " request watting"
                  ),
                    0 == this._requests.length &&
                      this.updateNetTips(o.Requesting, !1);
                }
                var i = this._listener[t];
                if (null != i)
                  for (var r = 0, s = i; r < s.length; r++) {
                    var c = s[r];
                    console.log("NetNode execute listener cmd " + t),
                      this._callbackExecuter(c, e);
                  }
              } else console.error("NetNode checkHead Error");
            }),
            (e.prototype.onError = function (e) {
              console.error(e);
            }),
            (e.prototype.onClosed = function () {
              var e = this;
              this.clearTimer(),
                !this._disconnectCallback || this._disconnectCallback()
                  ? this.isAutoReconnect()
                    ? (this.updateNetTips(o.ReConnecting, !0),
                      (this._reconnectTimer = setTimeout(function () {
                        e._socket.close(),
                          (e._state = a.Closed),
                          e.connect(e._connectOptions),
                          e._autoReconnect > 0 && (e._autoReconnect -= 1);
                      }, this._reconnetTimeOut)))
                    : (this._state = a.Closed)
                  : console.log("disconnect return!");
            }),
            (e.prototype.close = function (e, t) {
              this.clearTimer(),
                (this._listener = {}),
                (this._requests.length = 0),
                this._networkTips &&
                  (this._networkTips.connectTips(!1),
                  this._networkTips.reconnectTips(!1),
                  this._networkTips.requestTips(!1)),
                this._socket
                  ? this._socket.close(e, t)
                  : (this._state = a.Closed);
            }),
            (e.prototype.closeSocket = function (e, t) {
              this._socket && this._socket.close(e, t);
            }),
            (e.prototype.send = function (e, t) {
              return (
                void 0 === t && (t = !1),
                this._state == a.Working || t
                  ? (console.log("socket send ..."), this._socket.send(e))
                  : this._state == a.Checking || this._state == a.Connecting
                  ? (this._requests.push({
                      buffer: e,
                      rspCmd: 0,
                      rspObject: null,
                    }),
                    console.log(
                      "NetNode socket is busy, push to send buffer, current state is " +
                        this._state
                    ),
                    !0)
                  : (console.error(
                      "NetNode request error! current state is " + this._state
                    ),
                    !1)
              );
            }),
            (e.prototype.request = function (e, t, n, i, r) {
              void 0 === i && (i = !0),
                void 0 === r && (r = !1),
                (this._state == a.Working || r) && this._socket.send(e),
                console.log("NetNode request with timeout for " + t),
                this._requests.push({ buffer: e, rspCmd: t, rspObject: n }),
                i && this.updateNetTips(o.Requesting, !0);
            }),
            (e.prototype.requestUnique = function (e, t, n, o, a) {
              void 0 === o && (o = !0), void 0 === a && (a = !1);
              for (var i = 0; i < this._requests.length; ++i)
                if (this._requests[i].rspCmd == t)
                  return (
                    console.log("NetNode requestUnique faile for " + t), !1
                  );
              return this.request(e, t, n, o, a), !0;
            }),
            (e.prototype.setResponeHandler = function (e, t, n) {
              return null == t
                ? (console.error("NetNode setResponeHandler error " + e), !1)
                : ((this._listener[e] = [{ target: n, callback: t }]), !0);
            }),
            (e.prototype.addResponeHandler = function (e, t, n) {
              if (null == t)
                return (
                  console.error("NetNode addResponeHandler error " + e), !1
                );
              var o = { target: n, callback: t };
              return (
                null == this._listener[e]
                  ? (this._listener[e] = [o])
                  : -1 == this.getNetListenersIndex(e, o) &&
                    this._listener[e].push(o),
                !0
              );
            }),
            (e.prototype.removeResponeHandler = function (e, t, n) {
              if (null != this._listener[e] && null != t) {
                var o = this.getNetListenersIndex(e, {
                  target: n,
                  callback: t,
                });
                -1 != o && this._listener[e].splice(o, 1);
              }
            }),
            (e.prototype.cleanListeners = function (e) {
              void 0 === e && (e = -1),
                -1 == e ? (this._listener = {}) : (this._listener[e] = null);
            }),
            (e.prototype.getNetListenersIndex = function (e, t) {
              for (var n = -1, o = 0; o < this._listener[e].length; o++) {
                var a = this._listener[e][o];
                if (a.callback == t.callback && a.target == t.target) {
                  n = o;
                  break;
                }
              }
              return n;
            }),
            (e.prototype.resetReceiveMsgTimer = function () {
              var e = this;
              null !== this._receiveMsgTimer &&
                clearTimeout(this._receiveMsgTimer),
                (this._receiveMsgTimer = setTimeout(function () {
                  console.warn("NetNode recvieMsgTimer close socket!"),
                    e._socket.close();
                }, this._receiveTime));
            }),
            (e.prototype.resetHearbeatTimer = function () {
              var e = this;
              null !== this._keepAliveTimer &&
                clearTimeout(this._keepAliveTimer),
                (this._keepAliveTimer = setTimeout(function () {
                  console.log("NetNode keepAliveTimer send Hearbeat"),
                    e.send(e._protocolHelper.getHearbeat());
                }, this._heartTime));
            }),
            (e.prototype.clearTimer = function () {
              null !== this._receiveMsgTimer &&
                clearTimeout(this._receiveMsgTimer),
                null !== this._keepAliveTimer &&
                  clearTimeout(this._keepAliveTimer),
                null !== this._reconnectTimer &&
                  clearTimeout(this._reconnectTimer);
            }),
            (e.prototype.isAutoReconnect = function () {
              return 0 != this._autoReconnect;
            }),
            (e.prototype.rejectReconnect = function () {
              (this._autoReconnect = 0), this.clearTimer();
            }),
            e
          );
        })();
        (n.NetNode = i), cc._RF.pop();
      },
      {},
    ],
    NoNetworkView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "64e93MPsw9K55GkBwov+mQ8", "NoNetworkView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Native/NativeBridge"),
          u = e("../Framework/Utils/Utils"),
          d = cc._decorator,
          p = d.ccclass,
          f =
            (d.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  u.default.localStr(this.node);
                }),
                (t.prototype.start = function () {}),
                (t.prototype.onClickSettting = function () {
                  c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                    l.default.jumpToNetworkSettings();
                }),
                i([p], t)
              );
            })(r.default));
        (n.default = f), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    NodePool: [
      function (e, t) {
        "use strict";
        cc._RF.push(t, "79670Jcz25EHbpPz2sbGO5H", "NodePool"), cc._RF.pop();
      },
      {},
    ],
    OnlineRewardView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "0732deacLBEBbXt+nCruSEJ", "OnlineRewardView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Manager/TaskManager"),
          c = e("../Framework/Manager/UserInfoManager"),
          l = e("../Framework/Utils/Utils"),
          u = e("../Framework/Enum/GameEnum"),
          d = e("../Framework/Enum/GameConst"),
          p = e("../Framework/Manager/GameDataManager"),
          f = e("../Framework/Manager/BuriedPointManager"),
          h = e("../Framework/Native/NativeBridge"),
          g = e("../Framework/Manager/AudioManager"),
          m = cc._decorator,
          _ = m.ccclass,
          y = m.property,
          v = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.bar_reward = null),
                (t.node_gold = null),
                (t.label_gold = null),
                (t.node_dis = null),
                (t.label_dis = null),
                (t.label_time = null),
                (t.node_box_list = []),
                (t.node_guangxiao_list = []),
                (t.node_gold_pos = null),
                (t.node_dis_pos = null),
                (t.node_jiantou = null),
                (t.img_title = null),
                (t.endTime = 0),
                (t.updateNum = 0),
                (t.boxIndex = 1),
                (t._onlineRewardInfo = null),
                (t._onlineTimeNum = 0),
                (t.callback = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                var e = this;
                h.default.preloadReward(u.ADType.Online_Reward),
                  c.default.getInstance().isShowAppluck(!1),
                  (this.endTime = l.default.getCountdown()),
                  this.registerAllEvents(),
                  this.refrshUI(),
                  this.loadRes(
                    d.LANGUAGE_IMG_PATH +
                      l.default.getLanguagePath() +
                      "img_online_title",
                    cc.SpriteFrame,
                    function (t) {
                      e.img_title.spriteFrame = t;
                    }
                  ),
                  h.default.showBanner();
              }),
              (t.prototype.setCallBack = function (e) {
                this.callback = e;
              }),
              (t.prototype.refrshUI = function () {
                this.updateTime(),
                  (this._onlineRewardInfo = s.default
                    .getInstance()
                    .getOnlineRewardInfo()),
                  (this._onlineTimeNum = c.default
                    .getInstance()
                    .getOnlineTime());
                var e = 0,
                  t = 0,
                  n = 0,
                  o = function (o) {
                    var i = a.node_box_list[e]
                        .getChildByName("label_time")
                        .getComponent(cc.Label),
                      r = a.node_box_list[e]
                        .getChildByName("img_box")
                        .getComponent(cc.Sprite);
                    a.node_box_list[e]
                      .getChildByName("img_get")
                      .getComponent(cc.Sprite),
                      (i.string = l.default.replaceStr(
                        "onlinereward_mins",
                        a._onlineRewardInfo[o].time / 60
                      )),
                      (t = a._onlineRewardInfo[o].time / 60),
                      a._onlineRewardInfo[o].taskStatus == u.TaskStatus.Task_Got
                        ? a.loadRes(
                            d.ONLINE_REWARD +
                              "bx" +
                              a._onlineRewardInfo[o].id +
                              a._onlineRewardInfo[o].id +
                              a._onlineRewardInfo[o].id,
                            cc.SpriteFrame,
                            function (e) {
                              r.spriteFrame = e;
                            }
                          )
                        : a._onlineRewardInfo[o].taskStatus ==
                            u.TaskStatus.Task_NotCan &&
                          a._onlineTimeNum >= a._onlineRewardInfo[o].time
                        ? (a.loadRes(
                            d.ONLINE_REWARD +
                              "bx" +
                              a._onlineRewardInfo[o].id +
                              a._onlineRewardInfo[o].id,
                            cc.SpriteFrame,
                            function (e) {
                              r.spriteFrame = e;
                            }
                          ),
                          parseInt(o) > n && (n = parseInt(o)))
                        : a.loadRes(
                            d.ONLINE_REWARD + "bx" + a._onlineRewardInfo[o].id,
                            cc.SpriteFrame,
                            function (e) {
                              r.spriteFrame = e;
                            }
                          ),
                      e++;
                  },
                  a = this;
                for (var i in this._onlineRewardInfo) o(i);
                this.getRewardMaxIndex() > this.boxIndex &&
                  (this.boxIndex = this.getRewardMaxIndex()),
                  (this.bar_reward.progress = this._onlineTimeNum / 60 / t),
                  this.updateTip(),
                  this.setGuangxiao(n);
              }),
              (t.prototype.setGuangxiao = function (e) {
                for (var t = 0; t < this.node_guangxiao_list.length; t++)
                  t == e - 1
                    ? ((this.node_guangxiao_list[t].active = !0),
                      this.node_guangxiao_list[t].runAction(
                        cc.repeatForever(cc.rotateBy(3, 360))
                      ))
                    : (this.node_guangxiao_list[t].active = !1);
              }),
              (t.prototype.updateTip = function () {
                if (this._onlineRewardInfo[this.boxIndex]) {
                  var e =
                    this._onlineRewardInfo[this.boxIndex].reward.split(":");
                  e[0] && (this.label_gold.string = "" + e[0]),
                    e[1]
                      ? ((this.node_dis.active = !0),
                        (this.label_dis.string = "" + e[1]))
                      : (this.node_dis.active = !1);
                }
                this.node_jiantou.x = this.node_box_list[this.boxIndex - 1].x;
              }),
              (t.prototype.onBtnBoxReward = function (e, t) {
                if (
                  (g.default
                    .getInstance()
                    .playEffectWithPath(u.AudioType.Button_Click),
                  p.default.getInstance().getTools().showNoNetWorkTip())
                ) {
                  var n = parseInt(t);
                  this._onlineRewardInfo[n] &&
                    this.getRewardMaxIndex() == n &&
                    this._onlineRewardInfo[n].taskStatus ==
                      u.TaskStatus.Task_NotCan &&
                    this._onlineTimeNum >= this._onlineRewardInfo[n].time &&
                    this.getAllReward(n),
                    n != this.boxIndex &&
                      ((this.boxIndex = n),
                      this.updateTip(),
                      cc.director.emit(u.GameEvent.Get_Online_Reward));
                }
              }),
              (t.prototype.getRewardMaxIndex = function () {
                var e = 0;
                for (var t in this._onlineRewardInfo)
                  this._onlineRewardInfo[t].taskStatus ==
                    u.TaskStatus.Task_NotCan &&
                    this._onlineTimeNum >= this._onlineRewardInfo[t].time &&
                    parseInt(t) > e &&
                    (e = parseInt(t));
                return e;
              }),
              (t.prototype.getAllReward = function (e) {
                for (var t = this, n = 0, o = 0, a = 0, i = 1; i <= e; i++)
                  if (
                    this._onlineRewardInfo[i].taskStatus ==
                      u.TaskStatus.Task_NotCan &&
                    this._onlineTimeNum >= this._onlineRewardInfo[e].time
                  ) {
                    var r = this._onlineRewardInfo[i].reward.split(":");
                    if (((n += parseInt(r[0])), r[1])) {
                      var d = parseInt(r[1]);
                      o += d;
                    }
                    if (r[2]) {
                      var g = parseInt(r[2]);
                      a += g;
                    }
                  }
                h.default.watchVideo(function () {
                  var i = c.default.getInstance().getMyselfUserInfo(),
                    r = l.default.getWorldPosition(t.node_gold_pos);
                  if (
                    (t.setGuangxiao(999),
                    f.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: u.BuriedOneKey.goldEarnCount,
                        actionName: u.BuriedTwoKey.goldEarnTime,
                        value: n,
                      }),
                    p.default
                      .getInstance()
                      .getTools()
                      .playFlyEffect(u.FlyEffectType.Coins, r, n, function () {
                        i.setGoldNum(i.getGoldNum() + n);
                      }),
                    o)
                  ) {
                    var d = l.default.getWorldPosition(t.node_dis_pos);
                    p.default
                      .getInstance()
                      .getTools()
                      .playFlyEffect(
                        u.FlyEffectType.Diamonds,
                        d,
                        o,
                        function () {
                          i.setDiamondNum(i.getDiamondNum() + o);
                        }
                      ),
                      f.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: u.BuriedOneKey.diamondEarnCount,
                          actionName: u.BuriedTwoKey.diamondEarnTime,
                          value: o,
                        });
                  }
                  a &&
                    c.default
                      .getInstance()
                      .setSkinItemNum(
                        c.default.getInstance().getSkinItem() + a
                      ),
                    s.default
                      .getInstance()
                      .setOnlineReward(e, u.TaskStatus.Task_Got),
                    f.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: u.BuriedPointKey.OnlineReward,
                        id: e,
                      });
                }, u.ADType.Online_Reward);
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  u.GameEvent.Update_Online_Reward,
                  this.refrshUI,
                  this
                );
              }),
              (t.prototype.update = function (e) {
                (this.updateNum += e),
                  this.updateNum >= 1 &&
                    (this.endTime--, this.updateTime(), (this.updateNum = 0));
              }),
              (t.prototype.updateTime = function () {
                this.label_time.string = l.default.formatTime(this.endTime);
              }),
              (t.prototype.onBtnCloseClick = function () {
                var e = this;
                this.callback && this.callback(),
                  h.default.watchVideo(function () {
                    h.default.closeBanner(),
                      c.default.getInstance().isShowAppluck(!0),
                      cc.director.emit(u.GameEvent.Close_Parent_Ui),
                      e.onClose();
                  }, "onlineViewClose_Insert");
              }),
              i([y(cc.ProgressBar)], t.prototype, "bar_reward", void 0),
              i([y(cc.Node)], t.prototype, "node_gold", void 0),
              i([y(cc.Label)], t.prototype, "label_gold", void 0),
              i([y(cc.Node)], t.prototype, "node_dis", void 0),
              i([y(cc.Label)], t.prototype, "label_dis", void 0),
              i([y(cc.Label)], t.prototype, "label_time", void 0),
              i([y(cc.Node)], t.prototype, "node_box_list", void 0),
              i([y(cc.Node)], t.prototype, "node_guangxiao_list", void 0),
              i([y(cc.Node)], t.prototype, "node_gold_pos", void 0),
              i([y(cc.Node)], t.prototype, "node_dis_pos", void 0),
              i([y(cc.Node)], t.prototype, "node_jiantou", void 0),
              i([y(cc.Sprite)], t.prototype, "img_title", void 0),
              i([_], t)
            );
          })(r.default);
        (n.default = v), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/TaskManager": "TaskManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    PlayerInfo: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "f1735lYABdF6ZWHfDSk61Ol", "PlayerInfo");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Common/Dice"),
          s = e("../Framework/Base/BaseComponent"),
          c = e("../Framework/Enum/GameConst"),
          l = e("../Framework/Enum/GameEnum"),
          u = e("../Framework/Manager/AudioManager"),
          d = e("../Framework/Manager/BuriedPointManager"),
          p = e("../Framework/Manager/ChessManager"),
          f = e("../Framework/Manager/GameDataManager"),
          h = e("../Framework/Manager/LuckManager"),
          g = e("../Framework/Manager/RobotManager"),
          m = e("../Framework/Manager/RoomInfoManager"),
          _ = e("../Framework/Manager/ShopDataManager"),
          y = e("../Framework/Manager/TaskManager"),
          v = e("../Framework/Manager/UserInfoManager"),
          I = e("../Framework/Utils/Utils"),
          C = cc._decorator,
          k = C.ccclass,
          w = C.property,
          P = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_bg = null),
                (t.node_online = null),
                (t.node_online_list = []),
                (t.node_computer = null),
                (t.node_computer_list = []),
                (t.node_local = null),
                (t.node_local_list = []),
                (t.spfOutTime = null),
                (t.editNumber = null),
                (t.btn_audo = null),
                (t._userInfo = null),
                (t._labGold = null),
                (t._labDiamond = null),
                (t._sprCD = null),
                (t._sprCDRed = null),
                (t._perMinusValue = 0),
                (t._outTimeCount = 0),
                (t._imgHeadPhoto = null),
                (t._btnDice = null),
                (t._dice = null),
                (t._curRollDicePoints = -1),
                (t._sprCountry = null),
                (t._labCountryName = null),
                (t._sprOutTimes = []),
                (t._usePropsView = null),
                (t._sprArrow = null),
                (t._sprArrowOriginPos = null),
                (t._diceOriginScale = 0),
                (t._outBaseRollDiceCount = 0),
                (t._robotBaseRollDiceCount = 0),
                (t._labLuck = null),
                (t._isOneChessAgainRoll = !1),
                (t._sixPointsCount = 0),
                (t._diceAnimFinishCallback = null),
                (t._isOne = !0),
                (t._isRobot = !1),
                (t._robotPlayerIndex = 1),
                (t._InVerticalLine = 0),
                (t._robotInVerticalLine = 0),
                (t._diceNameList = [
                  "original",
                  "grass",
                  "sandbeach",
                  "snow",
                  "space",
                  "Indiastyle",
                ]),
                (t._player_opt_cd = 0),
                (t._imgPlayer = null),
                (t._firstSix = !0),
                (t._diceCount = 0),
                (t._img_expression_bg = null),
                (t._node_expression = null),
                (t._node_sentence = null),
                (t._label_sentence = null),
                (t._isTrusteeship = !1),
                (t._trusteeshipCount = 0),
                (t._isOutTime = !1),
                (t._diceNum = 0),
                (t._showUndoDiceNum = 0),
                (t._maskBg = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  (this._player_opt_cd = c.PLAYER_OPT_CD_TIME),
                  (m.default.getInstance().getGameMode() != l.GameMode.Local &&
                    m.default.getInstance().getGameMode() !=
                      l.GameMode.Computer) ||
                    (this._player_opt_cd = 999999),
                  m.default.getInstance().getRoomMode() ==
                  l.GameRoomMode.Classic
                    ? (this._showUndoDiceNum = 3)
                    : m.default.getInstance().getRoomMode() ==
                        l.GameRoomMode.Quick && (this._showUndoDiceNum = 2);
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  l.GameEvent.Turn_Player_Operation,
                  this.onOperation,
                  this
                ),
                  this.registerEvent(
                    l.GameEvent.Roll_The_Dice_Test,
                    this.onRollTheDiceTest,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.Update_Country_Code,
                    this.onUpdateCountry,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.Refresh_Player_Luck_Info,
                    this.onRefreshPlayerLuckInfo,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.delect_Expression,
                    this.delectExpression,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.twoRobat_Expression,
                    this.robotSendExpression,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.send_Sentence,
                    this.showSentence,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.Close_Undo_Dice,
                    this.setDicePoints,
                    this
                  ),
                  this.registerEvent(
                    l.GameEvent.Show_Undo_Node,
                    this.showButtonActive,
                    this
                  );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.setInfo = function (e, t) {
                var n = this;
                this._userInfo = e;
                var o = null,
                  a = m.default.getInstance().getGameMode();
                a == l.GameMode.Online ||
                a == l.GameMode.BombItem ||
                a == l.GameMode.Roadblock
                  ? ((this.node_online.active = !0),
                    (this.node_online_list[e.getPlayerIndex()].active = !0),
                    (o = this.node_online_list[e.getPlayerIndex()]),
                    (this.node_computer.active = !1),
                    (this.node_local.active = !1),
                    (this._img_expression_bg =
                      o.getChildByName("img_expression")),
                    (this._node_expression =
                      this._img_expression_bg.getChildByName(
                        "node_expression"
                      )),
                    (this._node_sentence = o.getChildByName("img_sentence")),
                    (this._label_sentence = this._node_sentence
                      .getChildByName("label_sentence")
                      .getComponent(cc.Label)))
                  : a == l.GameMode.Computer
                  ? ((this.node_online.active = !1),
                    (this.node_computer.active = !0),
                    (this.node_local.active = !1),
                    (this.node_computer_list[e.getPlayerIndex()].active = !0),
                    (o = this.node_computer_list[e.getPlayerIndex()]))
                  : ((this.node_online.active = !1),
                    (this.node_computer.active = !1),
                    (this.node_local.active = !0),
                    (this.node_local_list[e.getPlayerIndex()].active = !0),
                    (o = this.node_local_list[e.getPlayerIndex()]));
                var i = o.getChildByName("labCountry");
                (this._labCountryName = i.getComponent(cc.Label)),
                  (this._imgHeadPhoto = o.getChildByName("img_headphoto"));
                var s = o.getChildByName("img_head_select"),
                  u = o.getChildByName("img_head_select_red"),
                  d = o.getChildByName("labNickName"),
                  p = o.getChildByName("node_gold"),
                  f = p.getChildByName("labGold"),
                  h = o.getChildByName("labDimaond"),
                  g = o.getChildByName("labLuck"),
                  y = o.getChildByName("btnDice"),
                  v = o.getChildByName("Dice_" + this.getDiceIndex()),
                  C = o.getChildByName("sprArrow");
                (this._maskBg = o.getChildByName("img_mask")),
                  (this._dice = v.getComponent(r.default)),
                  (this._btnDice = y),
                  (this._sprArrow = C),
                  (this._sprArrowOriginPos = this._sprArrow.position),
                  (this._diceOriginScale = this._dice.node.scale),
                  (this._dice.node.active = !1),
                  (this._maskBg.active = !1),
                  (this._imgHeadPhoto.active = !0),
                  (this._sprCD = s.getComponent(cc.Sprite)),
                  (this._sprCD.node.active = !1),
                  (this._sprCDRed = u.getComponent(cc.Sprite)),
                  (this._sprCDRed.node.active = !1),
                  (this._labGold = f.getComponent(cc.Label)),
                  (this._labDiamond = h.getComponent(cc.Label)),
                  (this._labLuck = g.getComponent(cc.Label)),
                  (this._labLuck.node.color = cc.Color.RED),
                  (this._labLuck.fontSize = 30);
                var k =
                  c.PLAYER_HEAD_PHOTO_PATH +
                  "img_head_photo_" +
                  e.getHeadPhotoIdx();
                if (
                  (this.onUpdateGold(e.getGoldNum()),
                  this.onUpdateDiamond(e.getDiamondNum()),
                  this.onUpdateCountry(e.getCountryCode(), e.getCountryName()),
                  (o.getChildByName("nodeOuttime").active = !1),
                  _.default.getInstance().getSelectBoard(),
                  e.isMyself()
                    ? (this.registerEvent(
                        l.GameEvent.Update_Gold_Num,
                        this.onUpdateGold,
                        this
                      ),
                      this.registerEvent(
                        l.GameEvent.Update_Diamond_Num,
                        this.onUpdateDiamond,
                        this
                      ),
                      (this._usePropsView = t),
                      this._usePropsView.setInfo(this),
                      (d.getComponent(cc.Label).string =
                        I.default.replaceStr("game_you")),
                      m.default.getInstance().getGameMode() ==
                        l.GameMode.Local &&
                        (d.getComponent(cc.Label).string =
                          I.default.replaceStr("game_bule")),
                      this.loadRes(k, cc.SpriteFrame, function (e) {
                        n._imgHeadPhoto.getComponent(cc.Sprite).spriteFrame = e;
                      }))
                    : ((d.getComponent(cc.Label).string = I.default.replaceStr(
                        e.getNickName()
                      )),
                      a == l.GameMode.Computer
                        ? this.loadRes(
                            "img_local_computer",
                            cc.SpriteFrame,
                            function (e) {
                              n._imgHeadPhoto.getComponent(
                                cc.Sprite
                              ).spriteFrame = e;
                            }
                          )
                        : (a != l.GameMode.Online &&
                            a != l.GameMode.BombItem &&
                            a != l.GameMode.Roadblock) ||
                          this.loadRes(k, cc.SpriteFrame, function (e) {
                            n._imgHeadPhoto.getComponent(
                              cc.Sprite
                            ).spriteFrame = e;
                          })),
                  a == l.GameMode.Local)
                ) {
                  var w;
                  (w = e.isRobot() ? "img_local_computer" : "img_local_play"),
                    this.loadRes(w, cc.SpriteFrame, function (e) {
                      n._imgHeadPhoto.getComponent(cc.Sprite).spriteFrame = e;
                    });
                }
                p.active = !1;
                var P = I.default.savePointTwoNumber(e.getLuck());
                (this._labLuck.string = "Luck:" + P.toString()),
                  (this._labLuck.node.active = !1);
              }),
              (t.prototype.showExpression = function (e) {
                e.playerIndex == this._userInfo.getPlayerIndex() &&
                  this._img_expression_bg &&
                  ((this._img_expression_bg.active = !1),
                  (this._node_sentence.active = !1));
              }),
              (t.prototype.showSentence = function (e) {
                e.playerIndex == this._userInfo.getPlayerIndex() &&
                  (this._img_expression_bg &&
                    ((this._img_expression_bg.active = !1),
                    (this._node_sentence.active = !1)),
                  (this._label_sentence.string = I.default.replaceStr(
                    e.expressionName
                  )),
                  this.unschedule(this.delectSentence),
                  this.scheduleOnce(this.delectSentence, 2));
              }),
              (t.prototype.delectSentence = function () {
                this._node_sentence && (this._node_sentence.active = !1);
              }),
              (t.prototype.delectExpression = function (e) {
                e == this._userInfo.getPlayerIndex() &&
                  (this._img_expression_bg &&
                    (this._img_expression_bg.active = !1),
                  this._node_expression.removeAllChildren());
              }),
              (t.prototype.getDiceIndex = function () {
                for (
                  var e = 0, t = _.default.getInstance().getSelectDice(), n = 0;
                  n < this._diceNameList.length;
                  n++
                )
                  if (t == this._diceNameList[n]) {
                    e = n;
                    break;
                  }
                return e;
              }),
              (t.prototype.onClickDice = function () {
                this.setDiceButtonActive(!1);
                var e = m.default.getInstance().getGameMode();
                if (0 != f.default.getInstance().getUndoIndex()) {
                  this.undo(f.default.getInstance().getUndoIndex());
                  var t = f.default.getInstance().getGameUndoCount();
                  f.default.getInstance().setGameUndoCount(t - 1),
                    cc.director.emit(l.GameEvent.Use_Undo),
                    f.default.getInstance().setUndoIndex(0),
                    f.default.getInstance().setIsCompleteUndoPower(!0);
                } else
                  e == l.GameMode.Local
                    ? this.dice()
                    : v.default
                        .getInstance()
                        .getMyselfUserInfo()
                        .getPlayerIndex() == this._userInfo.getPlayerIndex() &&
                      (this.dice(), (this._trusteeshipCount = 0));
              }),
              (t.prototype.undo = function (e) {
                this.stopTurnPlayerAnim();
                var t = 1;
                switch (e) {
                  case 1:
                    t = I.default.getRandomNum(4, 6);
                    break;
                  case 2:
                    t = I.default.getRandomNum(1, 3);
                    break;
                  case 3:
                    var n = [1, 3, 5];
                    t = n[I.default.getRandomNum(1, n.length) - 1];
                    break;
                  case 4:
                    var o = [2, 4, 6];
                    t = o[I.default.getRandomNum(1, o.length) - 1];
                }
                this.setCurRollDicePoints(t), this.playDiceAnim(t, void 0);
              }),
              (t.prototype.dice = function () {
                this._diceCount++,
                  this.stopTurnPlayerAnim(),
                  this.rollTheDice(),
                  this._usePropsView &&
                    this._usePropsView.setDoubleDiceActive(!1),
                  f.default
                    .getInstance()
                    .setRoundCount(f.default.getInstance().getRoundCount() + 1);
              }),
              (t.prototype.getDicePoints = function (e) {
                var t,
                  n = p.default
                    .getInstance()
                    .playChessIsOutBase(this._userInfo.getPlayerIndex());
                return (
                  this._isRobot
                    ? (n
                        ? ((this._robotBaseRollDiceCount += 1),
                          (t = h.default
                            .getInstance()
                            .getRobot(this._robotBaseRollDiceCount)) ==
                            c.DICE_MAX_POINTS &&
                            (this._robotBaseRollDiceCount = 0))
                        : p.default
                            .getInstance()
                            .hasChessInVerticalLine(
                              this._userInfo.getPlayerIndex()
                            )
                        ? (this._robotInVerticalLine++,
                          (t = h.default
                            .getInstance()
                            .getDicePoints(
                              this._userInfo,
                              n,
                              this._robotInVerticalLine
                            )))
                        : ((this._robotInVerticalLine = 0),
                          (t = h.default
                            .getInstance()
                            .getDefaultDicePoints(
                              this._isRobot,
                              this._robotPlayerIndex
                            ))),
                      (m.default.getInstance().getGameMode() !=
                        l.GameMode.BombItem &&
                        m.default.getInstance().getGameMode() !=
                          l.GameMode.Roadblock) ||
                        g.default
                          .getInstance()
                          .robatBomb(this._userInfo.getPlayerIndex()),
                      console.log(
                        "\u673a\u5668\u4eba\u968f\u673a\u8981\u7684\u6570\u5b57\uff1a " +
                          t
                      ))
                    : (this._diceNum++,
                      n
                        ? ((this._outBaseRollDiceCount += 1),
                          (t = h.default
                            .getInstance()
                            .getDicePoints(
                              this._userInfo,
                              n,
                              this._outBaseRollDiceCount
                            )) == c.DICE_MAX_POINTS &&
                            (this._outBaseRollDiceCount = 0))
                        : this._isOne
                        ? ((t = h.default
                            .getInstance()
                            .getDicePoints(this._userInfo, n, 0, this._isOne)),
                          (this._isOne = !1))
                        : p.default
                            .getInstance()
                            .hasChessInVerticalLine(
                              v.default
                                .getInstance()
                                .getMyselfUserInfo()
                                .getPlayerIndex()
                            )
                        ? (this._InVerticalLine++,
                          (t = h.default
                            .getInstance()
                            .getDicePoints(
                              this._userInfo,
                              n,
                              this._InVerticalLine
                            )))
                        : ((t = h.default
                            .getInstance()
                            .getDicePoints(this._userInfo, n, 0)),
                          (this._InVerticalLine = 0)),
                      this.getNewPlayDicePoint() &&
                        (t = this.getNewPlayDicePoint())),
                  null != e && (t = e),
                  6 == t
                    ? (this._userInfo.getPlayerIndex() ==
                        l.PlayerIndex.LeftBottom &&
                        this._firstSix &&
                        (f.default
                          .getInstance()
                          .setFirstSixIndex(this._diceCount),
                        (this._firstSix = !1)),
                      (this._sixPointsCount += 1),
                      this._isRobot &&
                      1 == v.default.getInstance().getGameTotalRounds()
                        ? (t = h.default.getInstance().getNotSixDicePoints())
                        : this._sixPointsCount > 3 &&
                          ((t = h.default.getInstance().getNotSixDicePoints()),
                          (this._sixPointsCount = 0)))
                    : (this._sixPointsCount = 0),
                  m.default.getInstance().getGameMode() ==
                    l.GameMode.Computer ||
                  m.default.getInstance().getGameMode() == l.GameMode.Online
                    ? this._userInfo.getPlayerIndex() ==
                      l.PlayerIndex.LeftBottom
                      ? d.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: I.default.getEventName(),
                            actionName: l.BuriedTwoKey.playerDiceClick,
                            value: t,
                          })
                      : this._userInfo.getPlayerIndex() == l.PlayerIndex.LeftTop
                      ? d.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: I.default.getEventName(),
                            actionName: l.BuriedTwoKey.robot1DiceClick,
                            value: t,
                          })
                      : this._userInfo.getPlayerIndex() ==
                        l.PlayerIndex.RightTop
                      ? d.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: I.default.getEventName(),
                            actionName: l.BuriedTwoKey.robot2DiceClick,
                            value: t,
                          })
                      : this._userInfo.getPlayerIndex() ==
                          l.PlayerIndex.RightTop &&
                        d.default
                          .getInstance()
                          .sendBuriedPointInfo({
                            event: I.default.getEventName(),
                            actionName: l.BuriedTwoKey.robot3DiceClick,
                            value: t,
                          })
                    : this._userInfo.getPlayerIndex() ==
                      l.PlayerIndex.LeftBottom
                    ? d.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: I.default.getEventName(),
                          actionName: l.BuriedTwoKey.position1DiceClick,
                          value: t,
                        })
                    : this._userInfo.getPlayerIndex() == l.PlayerIndex.LeftTop
                    ? d.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: I.default.getEventName(),
                          actionName: l.BuriedTwoKey.position2DiceClick,
                          value: t,
                        })
                    : this._userInfo.getPlayerIndex() == l.PlayerIndex.RightTop
                    ? d.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: I.default.getEventName(),
                          actionName: l.BuriedTwoKey.position3DiceClick,
                          value: t,
                        })
                    : this._userInfo.getPlayerIndex() ==
                        l.PlayerIndex.RightTop &&
                      d.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: I.default.getEventName(),
                          actionName: l.BuriedTwoKey.position4DiceClick,
                          value: t,
                        }),
                  t
                );
              }),
              (t.prototype.playDiceAnim = function (e, t) {
                var n = this;
                (this._isOneChessAgainRoll = !1),
                  this._dice.playDiceAnim(e, function () {
                    if (
                      (n._diceAnimFinishCallback &&
                        n._diceAnimFinishCallback(e),
                      n._userInfo.isMyself())
                    ) {
                      if (n._usePropsView.isAgainRoll() && null == t) {
                        n._usePropsView.startAgainRollCD(),
                          y.default
                            .getInstance()
                            .setTaskProgress(l.TaskType.Task_dice, e),
                          e == c.DICE_MAX_POINTS &&
                            y.default
                              .getInstance()
                              .setTaskProgress(l.TaskType.Task_six);
                        var o = p.default
                          .getInstance()
                          .getPlayerCanWalkChess(
                            n._userInfo.getPlayerIndex(),
                            e
                          );
                        if (1 == o.length) {
                          n._isOneChessAgainRoll = !0;
                          for (var a = 0; a < o.length; a++)
                            o[a].setChessCanClick(!0);
                          return void f.default.getInstance().setDicePoints(e);
                        }
                      }
                      v.default.getInstance().getCompletedGuide() ||
                        (cc.director.emit(l.GameEvent.Show_Guide),
                        v.default.getInstance().setCompletedGuide(!0)),
                        cc.director.emit(l.GameEvent.Roll_The_Dice, e, t);
                    } else {
                      var i = I.default.getRandomNum(1, 2);
                      n.scheduleOnce(function () {
                        cc.director.emit(l.GameEvent.Roll_The_Dice, e, t);
                      }, i);
                    }
                  }),
                  u.default
                    .getInstance()
                    .playEffectWithPath(l.AudioType.Roll_Dice);
              }),
              (t.prototype.setDicePoints = function () {
                if (this._userInfo.isMyself()) {
                  var e = f.default.getInstance().getDicePoints();
                  e != this._curRollDicePoints
                    ? (this.setCurRollDicePoints(e),
                      this.playDiceAnim(e, void 0))
                    : (this.setCurRollDicePoints(e),
                      cc.director.emit(l.GameEvent.Roll_The_Dice, e, void 0));
                }
              }),
              (t.prototype.rollTheDice = function (e) {
                if (
                  ((this._userInfo.isMyself() ||
                    m.default.getInstance().getGameMode() ==
                      l.GameMode.Local) &&
                    (this.setDiceButtonActive(!1),
                    cc.director.emit(l.GameEvent.Hide_Dice_TestUI)),
                  1 == e)
                )
                  if (-1 == this._curRollDicePoints) {
                    var t = this.getDicePoints();
                    this.setCurRollDicePoints(t), this.playDiceAnim(t, e);
                  } else
                    cc.director.emit(
                      l.GameEvent.Roll_The_Dice,
                      this._curRollDicePoints,
                      e
                    );
                else
                  (t = this.getDicePoints()),
                    this.setCurRollDicePoints(t),
                    this.playDiceAnim(t, e);
              }),
              (t.prototype.delChess = function () {
                cc.director.emit(
                  l.GameEvent.Del_Player,
                  this._userInfo.getPlayerIndex()
                );
              }),
              (t.prototype.hidePlayerInfo = function () {
                this.node.active = !1;
              }),
              (t.prototype.addChess = function () {
                cc.director.emit(
                  l.GameEvent.Add_Player,
                  this._userInfo.getPlayerIndex()
                );
              }),
              (t.prototype.againRollCDOver = function () {
                this._isOneChessAgainRoll &&
                  ((this._isOneChessAgainRoll = !1),
                  -1 != this._curRollDicePoints &&
                    cc.director.emit(
                      l.GameEvent.Roll_The_Dice,
                      this._curRollDicePoints,
                      !1
                    ));
              }),
              (t.prototype.startCD = function () {
                this.setCurRollDicePoints(-1),
                  (m.default.getInstance().getGameMode() != l.GameMode.Online &&
                    m.default.getInstance().getGameMode() !=
                      l.GameMode.BombItem &&
                    m.default.getInstance().getGameMode() !=
                      l.GameMode.Roadblock) ||
                    (this._sprCD.node.active = !0),
                  (this._sprCD.fillRange = 1),
                  (this._sprCDRed.fillRange = 1);
                var e = this._player_opt_cd / 0.05;
                (this._perMinusValue = 1 / e),
                  this._userInfo.isMyself() &&
                    (this.playTurnPlayerAnim(),
                    this.setDiceButtonActive(!0),
                    this._usePropsView.setPropsCanUse(!0),
                    u.default
                      .getInstance()
                      .playEffectWithPath(l.AudioType.Turn_Player)),
                  this.schedule(this.cdTimer, 0.05);
              }),
              (t.prototype.cdTimer = function () {
                if (this._sprCD.fillRange - this._perMinusValue <= 0) {
                  (this._sprCD.fillRange = 0),
                    (this._sprCDRed.fillRange = 0),
                    this.closeCD(),
                    (this._outTimeCount += 1);
                  _.default.getInstance().getSelectBoard();
                  c.SKIN_PICTURE_PATH,
                    this._userInfo.isMyself() &&
                      cc.director.emit(l.GameEvent.Player_Operation_OutTime),
                    this.rollTheDice(!0),
                    (this._trusteeshipCount += 1),
                    f.default.getInstance().setUndoIndex(0),
                    m.default.getInstance().setIsOverTime(!0),
                    this.updateAudo();
                } else {
                  (this._sprCD.fillRange -= this._perMinusValue),
                    (this._sprCDRed.fillRange -= this._perMinusValue);
                  var e = 100 * this._sprCD.fillRange;
                  I.default.isEqualFloatNumber(e, 50)
                    ? ((this._sprCD.node.active = !1),
                      m.default.getInstance().getGameMode() ==
                        l.GameMode.Online && (this._sprCDRed.node.active = !0),
                      u.default
                        .getInstance()
                        .playEffectWithPath(l.AudioType.Player_Opt_CD))
                    : I.default.isEqualFloatNumber(e, 40) ||
                      I.default.isEqualFloatNumber(e, 30) ||
                      I.default.isEqualFloatNumber(e, 20) ||
                      I.default.isEqualFloatNumber(e, 10),
                    m.default.getInstance().setIsOverTime(!1),
                    this.updateAudo();
                }
              }),
              (t.prototype.setDiceRes = function (e, t) {
                this.loadRes(t, cc.SpriteFrame, function (t) {
                  e.spriteFrame = t;
                });
              }),
              (t.prototype.closeCD = function () {
                this.unschedule(this.cdTimer),
                  (this._sprCD.node.active = !1),
                  (this._sprCDRed.node.active = !1),
                  (this._perMinusValue = 0),
                  this.stopTurnPlayerAnim(),
                  this._userInfo.isMyself() &&
                    (this._usePropsView.reset(),
                    u.default.getInstance().stopAllEffect());
              }),
              (t.prototype.showButtonActive = function () {
                this._userInfo.isMyself() && this.setDiceButtonActive(!0);
              }),
              (t.prototype.restartCD = function () {
                var e = this;
                (this._isOneChessAgainRoll = !1),
                  this.rollTheDice(),
                  this.unschedule(this.cdTimer),
                  (this._sprCD.node.active = !1),
                  (this._sprCDRed.node.active = !1),
                  (this._perMinusValue = 0),
                  u.default.getInstance().stopAllEffect(),
                  (this._diceAnimFinishCallback = function (t) {
                    if (
                      ((e._diceAnimFinishCallback = null),
                      p.default
                        .getInstance()
                        .getPlayerCanWalkChess(e._userInfo.getPlayerIndex(), t)
                        .length > 0)
                    ) {
                      m.default.getInstance().getGameMode() ==
                        l.GameMode.Online && (e._sprCD.node.active = !0),
                        (e._sprCD.fillRange = 1),
                        (e._sprCDRed.fillRange = 1);
                      var n = e._player_opt_cd / 0.05;
                      (e._perMinusValue = 1 / n), e.schedule(e.cdTimer, 0.05);
                    }
                  });
              }),
              (t.prototype.onOperation = function (e) {
                var t = this,
                  n = m.default.getInstance().getGameMode(),
                  o = f.default.getInstance().getLocalInfo();
                if (e == this._userInfo.getPlayerIndex()) {
                  if (
                    ((this._dice.node.active = !0),
                    (this._imgHeadPhoto.active = !1),
                    (this._maskBg.active = !0),
                    this.startCD(),
                    (this._isRobot = !1),
                    e !=
                      v.default
                        .getInstance()
                        .getMyselfUserInfo()
                        .getPlayerIndex())
                  ) {
                    var a = I.default.getRandomNum(1, 3);
                    (n != l.GameMode.Local && n != l.GameMode.Computer) ||
                      (a = 0.01),
                      this.scheduleOnce(function () {
                        n == l.GameMode.Local
                          ? ((t._isRobot = o[e].isComputer),
                            console.log("this._isrobot: " + t._isRobot),
                            t._isRobot &&
                              (t.closeCD(),
                              (t._robotPlayerIndex = e),
                              t.rollTheDice()))
                          : (t.closeCD(),
                            (t._isRobot = !0),
                            (t._robotPlayerIndex = e),
                            t.rollTheDice());
                      }, a);
                  }
                  n == l.GameMode.Local &&
                    (this.setDiceButtonActive(!0), this.playTurnPlayerAnim()),
                    this._trusteeshipCount >= 3 &&
                      (this.closeCD(), this.rollTheDice(!0), this.updateAudo());
                } else
                  (this._dice.node.active = !1),
                    (this._imgHeadPhoto.active = !0),
                    (this._sprArrow.active = !1),
                    (this._maskBg.active = !1),
                    n == l.GameMode.Local && this.setDiceButtonActive(!1);
              }),
              (t.prototype.onRollTheDiceTest = function (e) {
                this.stopTurnPlayerAnim(), this.setDiceButtonActive(!1);
                var t = this.getDicePoints(e);
                this.setCurRollDicePoints(t),
                  this._dice.playDiceAnim(t, function () {
                    cc.director.emit(l.GameEvent.Roll_The_Dice, t);
                  }),
                  u.default
                    .getInstance()
                    .playEffectWithPath(l.AudioType.Roll_Dice);
              }),
              (t.prototype.onUpdateGold = function (e) {
                this._labGold.string = "" + e;
              }),
              (t.prototype.onUpdateDiamond = function (e) {
                this._labDiamond.string = "" + e;
              }),
              (t.prototype.onUpdateCountry = function () {}),
              (t.prototype.setDiceButtonActive = function (e) {
                this._btnDice.active = e;
              }),
              (t.prototype.setCurRollDicePoints = function (e) {
                this._curRollDicePoints = e;
              }),
              (t.prototype.playTurnPlayerAnim = function () {
                (this._sprArrow.position = this._sprArrowOriginPos),
                  (this._sprArrow.active = !0);
              }),
              (t.prototype.stopTurnPlayerAnim = function () {
                (this._sprArrow.active = !1),
                  this._dice.node.stopAllActions(),
                  (this._dice.node.scale = this._diceOriginScale);
              }),
              (t.prototype.testRollDice = function () {
                var e = parseInt(this.editNumber.string);
                cc.director.emit(
                  l.GameEvent.Roll_The_Dice_AI,
                  this._userInfo.getPlayerIndex(),
                  e
                );
              }),
              (t.prototype.onRefreshPlayerLuckInfo = function (e, t, n, o, a) {
                e == this._userInfo.getPlayerIndex() &&
                  ((this._labLuck.node.active = !1),
                  (t = I.default.savePointTwoNumber(t)),
                  null == n
                    ? (this._labLuck.string =
                        "\u5e78\u8fd0\u503c:" + t.toString())
                    : n
                    ? ((o = I.default.savePointTwoNumber(o)),
                      (this._labLuck.string =
                        "\u5e78\u8fd0\u503c:" +
                        t.toString() +
                        "\n\u5f53\u524d\u5728\u51fa\u57fa\u5730\u9636\u6bb5\n\u64476\u6982\u7387:" +
                        o))
                    : -1 == o
                    ? ((a = I.default.savePointTwoNumber(a)),
                      (this._labLuck.string =
                        "\u5e78\u8fd0\u503c:" +
                        t.toString() +
                        "\n\u68cb\u5b50\u8fc7\u534a\u6216\u8d70\u8fc7\u8ddd\u79bb\u8d85\u8fc72\u5708\n\u64474-6\u6982\u7387:" +
                        a))
                    : (this._labLuck.string =
                        "\u5e78\u8fd0\u503c:" +
                        t.toString() +
                        "\n\u9ed8\u8ba4\u6447\u8272\u5b50\u7b56\u7565"));
              }),
              (t.prototype.onBtnAutoClick = function () {
                (this._trusteeshipCount = 0), this.updateAudo();
              }),
              (t.prototype.updateAudo = function () {
                this.btn_audo.active = this._trusteeshipCount >= 3;
              }),
              (t.prototype.robotSendExpression = function (e) {
                var t = I.default.getRandomNum(3, 8);
                this.scheduleOnce(function () {
                  cc.director.emit(l.GameEvent.send_Expression, e);
                }, t);
              }),
              (t.prototype.getNewPlayDicePoint = function () {
                var e = 0;
                return (
                  (m.default.getInstance().getRoomMode() !=
                    l.GameRoomMode.Classic &&
                    m.default.getInstance().getComputerRoomMode() !=
                      l.GameRoomMode.Classic) ||
                  1 != v.default.getInstance().getGameTotalRounds()
                    ? (m.default.getInstance().getRoomMode() !=
                        l.GameRoomMode.Quick &&
                        m.default.getInstance().getComputerRoomMode() !=
                          l.GameRoomMode.Quick) ||
                      1 != v.default.getInstance().getGameTotalRounds() ||
                      (1 == this._diceNum
                        ? (e = 5)
                        : 2 == this._diceNum && (e = 3))
                    : 1 == this._diceNum
                    ? (e = 6)
                    : 2 == this._diceNum
                    ? (e = 5)
                    : 3 == this._diceNum && (e = 3),
                  e
                );
              }),
              i([w(cc.Sprite)], t.prototype, "img_bg", void 0),
              i([w(cc.Node)], t.prototype, "node_online", void 0),
              i([w(cc.Node)], t.prototype, "node_online_list", void 0),
              i([w(cc.Node)], t.prototype, "node_computer", void 0),
              i([w(cc.Node)], t.prototype, "node_computer_list", void 0),
              i([w(cc.Node)], t.prototype, "node_local", void 0),
              i([w(cc.Node)], t.prototype, "node_local_list", void 0),
              i([w(cc.SpriteFrame)], t.prototype, "spfOutTime", void 0),
              i([w(cc.EditBox)], t.prototype, "editNumber", void 0),
              i([w(cc.Node)], t.prototype, "btn_audo", void 0),
              i([k], t)
            );
          })(s.default);
        (n.default = P), cc._RF.pop();
      },
      {
        "../Common/Dice": "Dice",
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/ChessManager": "ChessManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/LuckManager": "LuckManager",
        "../Framework/Manager/RobotManager": "RobotManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/ShopDataManager": "ShopDataManager",
        "../Framework/Manager/TaskManager": "TaskManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    QuitGameSettingView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "0a46cJIXqVI4ZeP3mbUNCiQ", "QuitGameSettingView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/CirculateManager"),
          d = e("../Framework/Manager/RoomInfoManager"),
          p = e("../Framework/Manager/UserInfoManager"),
          f = e("../Framework/Native/NativeBridge"),
          h = e("../Framework/Utils/Utils"),
          g = cc._decorator,
          m = g.ccclass,
          _ = g.property,
          y = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (t.sprMusicStatus = []), (t.sprAudioStatus = []), t;
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                h.default.localStr(this.node), this.refreshButtonStatus();
              }),
              (t.prototype.refreshButtonStatus = function () {
                var e = p.default.getInstance().getGameSettingInfo();
                (this.sprMusicStatus[0].active = e.musicStatus),
                  (this.sprMusicStatus[1].active = !e.musicStatus),
                  (this.sprAudioStatus[0].active = e.effectStatus),
                  (this.sprAudioStatus[1].active = !e.effectStatus);
              }),
              (t.prototype.onClickMusic = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = p.default
                  .getInstance()
                  .getGameSettingInfo().musicStatus;
                e
                  ? l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: h.default.getEventName(),
                        actionName: s.BuriedTwoKey.closeBGM,
                      })
                  : l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: h.default.getEventName(),
                        actionName: s.BuriedTwoKey.openBGM,
                      }),
                  p.default.getInstance().setGameSettingInfo(!e, null),
                  c.default.getInstance().setMusicOpen(!e),
                  this.refreshButtonStatus();
              }),
              (t.prototype.onClickAudio = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = p.default
                  .getInstance()
                  .getGameSettingInfo().effectStatus;
                p.default.getInstance().setGameSettingInfo(null, !e),
                  c.default.getInstance().setEffectOpen(!e),
                  this.refreshButtonStatus(),
                  e
                    ? l.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: h.default.getEventName(),
                          actionName: s.BuriedTwoKey.closeSound,
                        })
                    : l.default
                        .getInstance()
                        .sendBuriedPointInfo({
                          event: h.default.getEventName(),
                          actionName: s.BuriedTwoKey.openSound,
                        });
              }),
              (t.prototype.onClickExit = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = d.default.getInstance().getGameMode(),
                  t = "";
                e == s.GameMode.Online
                  ? (t = s.ADType.ShowOlExit)
                  : e == s.GameMode.Computer
                  ? (t = s.ADType.ShowPcExit)
                  : e == s.GameMode.BombItem || e == s.GameMode.Roadblock
                  ? ((u.default.getInstance().isPlayAgain = !0),
                    (u.default.getInstance().isActivitying = !1))
                  : (t = s.ADType.ShowLocalExit),
                  f.default.watchVideo(function () {
                    cc.director.emit(s.GameEvent.Show_Quit_Prize_View);
                  }, t);
              }),
              i([_(cc.Node)], t.prototype, "sprMusicStatus", void 0),
              i([_(cc.Node)], t.prototype, "sprAudioStatus", void 0),
              i([m], t)
            );
          })(r.default);
        (n.default = y), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/CirculateManager": "CirculateManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    QuitGameView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "83f68mJ+VpARYu56suu4qLT", "QuitGameView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Native/NativeBridge"),
          d = e("../Framework/Utils/Utils"),
          p = cc._decorator,
          f = p.ccclass,
          h =
            (p.property,
            (function (e) {
              function t() {
                var t = (null !== e && e.apply(this, arguments)) || this;
                return (t._callback = null), t;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  d.default.localStr(this.node),
                    l.default.getInstance().getTools().getGlobalJson().info[0]
                      .show_quit_hall_insert &&
                      u.default.watchVideo(function () {},
                      s.ADType.Hall_Quit_Insert);
                }),
                (t.prototype.setInfo = function (e) {
                  this._callback = e;
                }),
                (t.prototype.onClickYes = function () {
                  c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                    this._callback &&
                      this._callback(s.PopupButtonClickType.Yes),
                    this.onClose();
                }),
                (t.prototype.onClickCancel = function () {
                  c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                    this._callback &&
                      this._callback(s.PopupButtonClickType.Cancel),
                    this.onClose();
                }),
                i([f], t)
              );
            })(r.default));
        (n.default = h), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    QuitPrizeView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "964d42ZJI1HeKRitZaGmQyz", "QuitPrizeView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/RoomInfoManager"),
          d = e("../Framework/Native/NativeBridge"),
          p = e("../Framework/Utils/Utils"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (t.labPrize = null), (t._callBack = null), t;
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                p.default.localStr(this.node);
              }),
              (t.prototype.setInfo = function (e, t) {
                void 0 === t && (t = null),
                  (this.labPrize.string = e.toString()),
                  (this._callBack = t);
              }),
              (t.prototype.onClickYes = function () {
                var e = this;
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var t,
                  n = l.default.getInstance().getTools().getGlobalJson()
                    .info[0].show_quit_game_insert;
                (t =
                  u.default.getInstance().getGameMode() == s.GameMode.Online
                    ? s.ADType.ShowOlExit
                    : u.default.getInstance().getGameMode() ==
                      s.GameMode.Computer
                    ? s.ADType.ShowPcExit
                    : s.ADType.ShowLocalExit),
                  n &&
                    d.default.watchVideo(function () {
                      e.onClose(),
                        cc.director.emit(
                          s.GameEvent.Bakc_To_Hall,
                          s.MidwayQuitType.Quit
                        );
                    }, t);
              }),
              (t.prototype.onClickCancel = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click),
                  this.onBtnCloseClick();
              }),
              (t.prototype.onBtnCloseClick = function () {
                this._callBack && this._callBack(), this.onClose();
              }),
              i([g(cc.Label)], t.prototype, "labPrize", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    ResKeeper: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "e7548uPzG1IHbJAG5JOhIeu", "ResKeeper");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.ResKeeper = void 0);
        var r = e("./ResLoader"),
          s = cc._decorator.ccclass,
          c = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (t.resCache = new Set()), t;
            }
            return (
              a(t, e),
              (t.prototype.load = function () {
                var e = this;
                if (
                  arguments.length < 2 ||
                  "function" != typeof arguments[arguments.length - 1]
                )
                  console.error("load faile, completed callback not found");
                else {
                  var t = arguments[arguments.length - 1];
                  (arguments[arguments.length - 1] = function (n, o) {
                    n ||
                      (o instanceof Array
                        ? o.forEach(function (t) {
                            e.cacheAsset(t);
                          })
                        : e.cacheAsset(o)),
                      t();
                  }),
                    r.default.load.apply(r.default, arguments);
                }
              }),
              (t.prototype.cacheAsset = function (e) {
                this.resCache.has(e) || (e.addRef(), this.resCache.add(e));
              }),
              (t.prototype.onDestroy = function () {
                this.releaseAssets();
              }),
              (t.prototype.releaseAssets = function () {
                this.resCache.forEach(function (e) {
                  e.decRef();
                }),
                  this.resCache.clear();
              }),
              i([s], t)
            );
          })(cc.Component);
        (n.ResKeeper = c), cc._RF.pop();
      },
      { "./ResLoader": "ResLoader" },
    ],
    ResLeakChecker: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "9487ex5I5NG3qnus+fkql3x", "ResLeakChecker"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.ResLeakChecker = void 0);
        var o = e("./ResUtil"),
          a = (function () {
            function e() {
              (this.resFilter = null),
                (this._checking = !1),
                (this.traceAssets = new Set());
            }
            return (
              (e.prototype.checkFilter = function (e) {
                return (
                  !!this._checking && (!this.resFilter || this.resFilter(e))
                );
              }),
              (e.prototype.traceAsset = function (e) {
                this.checkFilter(e) &&
                  (this.traceAssets.has(e) ||
                    (e.addRef(), this.extendAsset(e), this.traceAssets.add(e)));
              }),
              (e.prototype.extendAsset = function (e) {
                var t = e.addRef,
                  n = e.decRef,
                  a = new Map();
                (e["@traceMap"] = a),
                  (e.addRef = function () {
                    var n = o.ResUtil.getCallStack(1),
                      i = a.has(n) ? a.get(n) + 1 : 1;
                    return a.set(n, i), t.apply(e, arguments);
                  }),
                  (e.decRef = function () {
                    var t = o.ResUtil.getCallStack(1),
                      i = a.has(t) ? a.get(t) + 1 : 1;
                    return a.set(t, i), n.apply(e, arguments);
                  });
              }),
              (e.prototype.resetAsset = function (e) {
                e["@traceMap"] &&
                  (delete e.addRef, delete e.decRef, delete e["@traceMap"]);
              }),
              (e.prototype.untraceAsset = function (e) {
                this.traceAssets.has(e) &&
                  (this.resetAsset(e), e.decRef(), this.traceAssets.delete(e));
              }),
              (e.prototype.startCheck = function () {
                this._checking = !0;
              }),
              (e.prototype.stopCheck = function () {
                this._checking = !1;
              }),
              (e.prototype.getTraceAssets = function () {
                return this.traceAssets;
              }),
              (e.prototype.reset = function () {
                var e = this;
                this.traceAssets.forEach(function (t) {
                  e.resetAsset(t), t.decRef();
                }),
                  this.traceAssets.clear();
              }),
              (e.prototype.dump = function () {
                this.traceAssets.forEach(function (e) {
                  var t = e["@traceMap"];
                  t &&
                    t.forEach(function (e, t) {
                      console.log(e + " : " + t + " ");
                    });
                });
              }),
              e
            );
          })();
        (n.ResLeakChecker = a), cc._RF.pop();
      },
      { "./ResUtil": "ResUtil" },
    ],
    ResLoader: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "4b081G1b9pJvbDtVt9AUhXd", "ResLoader"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.resLoader = void 0);
        var o = e("./ResManager"),
          a = cc.js.isChildClassOf;
        a || (a = cc.isChildClassOf);
        var i = (function () {
          function e() {}
          return (
            (e.getLoader = function () {
              return cc.loader;
            }),
            (e.makeLoadArgs = function () {
              do {
                if (arguments.length < 2) break;
                var e = {};
                if (
                  "string" == typeof arguments[1] ||
                  arguments[1] instanceof Array
                ) {
                  if ("string" != typeof arguments[0]) break;
                  (e.bundle = arguments[0]),
                    (e.url = arguments[1]),
                    arguments.length > 2 &&
                      a(arguments[2], cc.Asset) &&
                      (e.type = arguments[2]);
                } else {
                  if (
                    !(
                      "string" == typeof arguments[0] ||
                      arguments[0] instanceof Array
                    )
                  )
                    break;
                  (e.url = arguments[0]),
                    a(arguments[1], cc.Asset) && (e.type = arguments[1]);
                }
                return (
                  "function" == typeof arguments[arguments.length - 1] &&
                    ((e.onCompleted = arguments[arguments.length - 1]),
                    "function" != typeof arguments[arguments.length - 2] ||
                      a(arguments[arguments.length - 2], cc.Asset) ||
                      (e.onProgess = arguments[arguments.length - 2])),
                  e
                );
              } while (0);
              return console.error("makeLoadArgs error " + arguments), null;
            }),
            (e.makeReleaseArgs = function () {
              do {
                if (arguments.length < 1) break;
                var e = {};
                return (
                  a(arguments[arguments.length - 1], cc.Asset) &&
                    (e.type = arguments[arguments.length - 1]),
                  arguments.length > 1 &&
                  "string" == typeof arguments[0] &&
                  ("string" == typeof arguments[1] ||
                    arguments[1] instanceof Array)
                    ? ((e.bundle = arguments[0]), (e.url = arguments[1]))
                    : (e.url = arguments[0]),
                  e
                );
              } while (0);
              return console.error("makeLoadArgs error " + arguments), null;
            }),
            (e.makeFinishCallback = function (e) {
              return (
                console.time("load|" + e.url),
                function (t, n) {
                  t ||
                    (n instanceof Array
                      ? n.forEach(function (e) {
                          o.default.Instance.cacheAsset(e);
                        })
                      : o.default.Instance.cacheAsset(n)),
                    e.onCompleted && e.onCompleted(t, n),
                    console.timeEnd("load|" + e.url);
                }
              );
            }),
            (e.getUuid = function (e, t) {
              return cc.resources.getInfoWithPath(e, t).uuid;
            }),
            (e.load = function () {
              var t = e.makeLoadArgs.apply(e, arguments),
                n = e.makeFinishCallback(t),
                o = e.getLoader();
              if ("string" == typeof t.url) {
                var a = cc.resources.getInfoWithPath(t.url, t.type),
                  i = a.uuid;
                i
                  ? o.loadRes(t.url, t.type, t.onProgess, n)
                  : o.load(t.url, t.onProgess, n);
              } else o.loadResArray(t.url, t.type, t.onProgess, n);
            }),
            (e.loadDir = function () {
              var t = e.makeLoadArgs.apply(e, arguments),
                n = e.makeFinishCallback(t),
                o = e.getLoader();
              o.loadResDir(t.url, t.type, t.onProgess, n);
            }),
            (e.release = function () {
              var t = e.makeReleaseArgs.apply(e, arguments);
              t.url instanceof Array
                ? t.url.forEach(function (n) {
                    t.type
                      ? o.default.Instance.releaseAsset(e.getUuid(n, t.type))
                      : o.default.Instance.releaseAsset(n);
                  })
                : t.type && "string" == typeof t.url
                ? o.default.Instance.releaseAsset(e.getUuid(t.url, t.type))
                : o.default.Instance.releaseAsset(t.url);
            }),
            e
          );
        })();
        (n.default = i), (n.resLoader = i), cc._RF.pop();
      },
      { "./ResManager": "ResManager" },
    ],
    ResManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "057d16YWG1BLYw+M2uo2hYT", "ResManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("./ResKeeper"),
          a = e("./ResUtil"),
          i = cc.loader,
          r = (function () {
            function e() {
              var t = this;
              (this.defaultKeeper = new o.ResKeeper()),
                (this.persistDepends = new Set()),
                (this.sceneDepends = null),
                (this.lastScene = null),
                cc.game.once(cc.game.EVENT_ENGINE_INITED, e.assetInit),
                cc.director.on(
                  cc.Director.EVENT_BEFORE_SCENE_LAUNCH,
                  function (e) {
                    t.onSceneChange(e);
                  }
                );
            }
            return (
              (e.prototype.getPersistDepends = function () {
                var e = cc.game,
                  t = Object.keys(e._persistRootNodes).map(function (t) {
                    return e._persistRootNodes[t];
                  });
                return a.ResUtil.getNodesDepends(t);
              }),
              (e.prototype.onSceneChange = function (e) {
                var t = this;
                if ((console.log("On Scene Change"), this.lastScene != e)) {
                  var n = null;
                  if (e.dependAssets instanceof Array) n = e.dependAssets;
                  else {
                    var o = i.getItem(e.uuid);
                    if (!o) return void console.error("cache scene faile " + e);
                    n = o.dependKeys;
                  }
                  for (var a = 0; a < n.length; ++a)
                    this.persistDepends.has(n[a]) || this.cacheAsset(n[a]);
                  var r = this.getPersistDepends();
                  if (this.sceneDepends)
                    for (a = 0; a < this.sceneDepends.length; ++a)
                      r.has(this.sceneDepends[a])
                        ? this.persistDepends.add(this.sceneDepends[a])
                        : this.persistDepends.has(this.sceneDepends[a]) ||
                          this.releaseAsset(this.sceneDepends[a]);
                  this.persistDepends.forEach(function (e) {
                    r.has(e) || (t.releaseAsset(e), t.persistDepends.delete(e));
                  }),
                    this.getKeeper().releaseAssets(),
                    (this.lastScene = e);
                }
              }),
              (e.assetInit = function () {
                console.log("asset init"),
                  Object.getOwnPropertyDescriptor(
                    cc.Asset.prototype,
                    "addRef"
                  ) ||
                    Object.defineProperties(cc.Asset.prototype, {
                      refDepends: {
                        configurable: !0,
                        writable: !0,
                        enumerable: !1,
                        value: !1,
                      },
                      refCount: {
                        configurable: !0,
                        writable: !0,
                        enumerable: !1,
                        value: 0,
                      },
                      addRef: {
                        configurable: !0,
                        writable: !0,
                        value: function () {
                          return ++this.refCount, this;
                        },
                      },
                      decRef: {
                        configurable: !0,
                        writable: !0,
                        value: function (t) {
                          return (
                            void 0 === t && (t = !0),
                            --this.refCount,
                            this.refCount <= 0 &&
                              t &&
                              e.Instance.releaseAsset(this),
                            this
                          );
                        },
                      },
                    });
              }),
              Object.defineProperty(e, "Instance", {
                get: function () {
                  return (
                    this.instance || (this.instance = new e()), this.instance
                  );
                },
                enumerable: !1,
                configurable: !0,
              }),
              (e.prototype.getKeeper = function () {
                return this.defaultKeeper;
              }),
              (e.prototype.getReferenceKey = function (e) {
                return e instanceof cc.Asset && !e._uuid && e.url
                  ? e.url
                  : i._getReferenceKey(e);
              }),
              (e.prototype.cacheItem = function (e) {
                if (e) {
                  var t = e.content;
                  if (t instanceof cc.Asset) {
                    if ((t.addRef(), !t.refDepends && e.dependKeys)) {
                      for (var n = e.dependKeys, o = 0; o < n.length; o++)
                        this.cacheItem(i.getItem(n[o]));
                      t.refDepends = !0;
                    }
                  } else
                    console.log("cacheItem " + e + " is not cc.Asset " + t);
                } else console.warn("cacheItem error, item is " + e);
              }),
              (e.prototype.cacheAsset = function (e) {
                var t = this.getReferenceKey(e);
                if (t) {
                  var n = i.getItem(t);
                  n
                    ? this.cacheItem(n)
                    : console.warn(
                        "cacheAsset error, loader.getItem " + t + " is " + n
                      );
                } else
                  console.warn(
                    "cacheAsset error, this.getReferenceKey " +
                      e +
                      " return " +
                      t
                  );
              }),
              (e.prototype.releaseItem = function (e, t) {
                if ((void 0 === t && (t = !1), e && e.content)) {
                  var n = e.content,
                    o = e.uuid || e.id;
                  if (n instanceof cc.Asset) {
                    if ((t && n.decRef(!1), n.refCount <= 0)) {
                      var a = e.dependKeys;
                      if (a)
                        for (var r = 0; r < a.length; r++)
                          this.releaseItem(i.getItem(a[r]), !0);
                      i.release(o), cc.log("loader.release cc.Asset " + o);
                    }
                  } else
                    i.release(o),
                      cc.log("loader.release " + o + " rawAsset " + n);
                } else console.warn("releaseItem error, item is " + e);
              }),
              (e.prototype.releaseAsset = function (e) {
                var t = this.getReferenceKey(e);
                if (t) {
                  var n = i.getItem(t);
                  n
                    ? this.releaseItem(n)
                    : console.warn(
                        "releaseAsset error, loader.getItem " + t + " is " + n
                      );
                } else
                  console.warn(
                    "releaseAsset error, this.getReferenceKey " +
                      e +
                      " return " +
                      t
                  );
              }),
              e
            );
          })();
        (n.default = r), cc._RF.pop();
      },
      { "./ResKeeper": "ResKeeper", "./ResUtil": "ResUtil" },
    ],
    ResPool: [
      function (e, t) {
        "use strict";
        cc._RF.push(t, "4d239KZe5hI4Zb4kyjxarWh", "ResPool"), cc._RF.pop();
      },
      {},
    ],
    ResUtil: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "8f503HZlhxLTY5UPaFTxC1e", "ResUtil"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.ResUtil = void 0);
        var o = e("./ResKeeper"),
          a = e("./ResManager");
        function i(e, t) {
          var n = cc.loader.getItem(e);
          if (n) {
            var o = n.dependKeys;
            if (o)
              for (var a = 0; a < o.length; a++) {
                var r = o[a];
                t.has(r) || (t.add(r), i(r, t));
              }
          }
        }
        function r(e, t) {
          if (e._uuid) {
            var n = cc.loader._getReferenceKey(e);
            t.has(n) || (t.add(n), i(n, t));
          }
        }
        function s(e, t) {
          for (
            var n = Object.getOwnPropertyNames(e), o = 0;
            o < n.length;
            o++
          ) {
            var a = e[n[o]];
            if ("object" == typeof a && a)
              if (Array.isArray(a))
                for (var i = 0; i < a.length; i++)
                  (c = a[i]) instanceof cc.Asset && r(c, t);
              else if (a.constructor && a.constructor !== Object)
                a instanceof cc.Asset && r(a, t);
              else {
                var s = Object.getOwnPropertyNames(a);
                for (i = 0; i < s.length; i++) {
                  var c;
                  (c = a[s[i]]) instanceof cc.Asset && r(c, t);
                }
              }
          }
        }
        function c(e, t) {
          for (var n = 0; n < e._components.length; n++) s(e._components[n], t);
          for (n = 0; n < e._children.length; n++) c(e._children[n], t);
        }
        var l = (function () {
          function e() {}
          return (
            (e.load = function () {
              for (
                var t = arguments[0],
                  n = e.getResKeeper(t),
                  o = new Array(),
                  a = 1;
                a < arguments.length;
                ++a
              )
                o[a - 1] = arguments[a];
              n.load.apply(n, o);
            }),
            (e.getResKeeper = function (t, n) {
              return t
                ? t.getComponent(o.ResKeeper) ||
                    (n
                      ? t.addComponent(o.ResKeeper)
                      : e.getResKeeper(t.parent, n))
                : a.default.Instance.getKeeper();
            }),
            (e.assignWith = function (t, n, o) {
              var a = e.getResKeeper(n, o);
              return a && t instanceof cc.Asset
                ? (a.cacheAsset(t), t)
                : (console.error("assignWith " + t + " to " + n + " faile"),
                  null);
            }),
            (e.instantiate = function (t) {
              var n = cc.instantiate(t),
                o = e.getResKeeper(n, !0);
              return o && o.cacheAsset(t), n;
            }),
            (e.getNodesDepends = function (e) {
              for (var t = new Set(), n = 0; n < e.length; n++) c(e[n], t);
              return t;
            }),
            (e.findCharPos = function (e, t, n) {
              for (var o = e.indexOf(t), a = o, i = 0; i < n; i++) {
                if (-1 == (o = e.indexOf(t, o + 1))) return a;
                a = o;
              }
              return a;
            }),
            (e.getCallStack = function (t) {
              var n = new Error().stack,
                o = e.findCharPos(n, "\n", t);
              return o > 0 && (n = n.slice(o)), n;
            }),
            e
          );
        })();
        (n.ResUtil = l), cc._RF.pop();
      },
      { "./ResKeeper": "ResKeeper", "./ResManager": "ResManager" },
    ],
    RewardDoubleView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "5ace1bdL1xDKJm3g91aiaCo", "RewardDoubleView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameEnum"),
          c = e("../../Framework/Manager/BuriedPointManager"),
          l = e("../../Framework/Native/NativeBridge"),
          u = e("../../Framework/Manager/GameDataManager"),
          d = e("../../Framework/Manager/AudioManager"),
          p = e("../../Framework/Utils/Utils"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labRewardCoinsTop = null),
                (t.labRewardCoinsBottom = null),
                (t.btn_close = null),
                (t.img_clock = null),
                (t.label_clock_reward = null),
                (t.label_txt = []),
                (t._rewardCoins = 0),
                (t.clockList = [
                  -223, -133, -133, -45, -45, 45, 45, 133, 133, 223,
                ]),
                (t.clockMultiple = [3, 2, 5, 2, 3]),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                var e = this;
                p.default.localStr(this.node),
                  c.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedOneKey.luckyWheel,
                      actionName: s.BuriedTwoKey.victoryShow,
                    });
                var t = u.default.getInstance().getTools().getGlobalJson();
                this.scheduleOnce(function () {
                  e.btn_close.node.active = !0;
                }, t.info[0].delay_close);
                var n = cc.moveTo(1, -223, this.img_clock.node.y),
                  o = cc.moveTo(1, 223, this.img_clock.node.y),
                  a = cc.sequence([n, o]),
                  i = cc.repeatForever(a);
                this.img_clock.node.runAction(i);
                for (var r = 0; r < this.clockMultiple.length; r++)
                  this.label_txt[r].string = "x" + this.clockMultiple[r];
              }),
              (t.prototype.setInfo = function (e) {
                (this._rewardCoins = e),
                  (this.labRewardCoinsTop.string = p.default.replaceStr(
                    "wheel_win",
                    e
                  )),
                  (this.labRewardCoinsBottom.string =
                    e + "x2=" + 2 * e + "coins");
              }),
              (t.prototype.onClickClose = function () {
                c.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: s.BuriedPointKey.TurntableReward,
                    isDoubleUp: !0,
                    rewardCoins: this._rewardCoins,
                  }),
                  cc.director.emit(
                    s.GameEvent.Turntable_Show_Get_Reward,
                    this._rewardCoins
                  ),
                  c.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedOneKey.goldEarnCount,
                      actionName: s.BuriedTwoKey.goldEarnWheel,
                      value: this._rewardCoins,
                    }),
                  this.onClose();
              }),
              (t.prototype.getClockRewardDouble = function () {
                for (
                  var e = this.img_clock.node.x, t = 0, n = 0;
                  n < this.clockList.length / 2;
                  n++
                )
                  if (
                    this.clockList[2 * n] <= e &&
                    this.clockList[2 * n + 1] >= e
                  ) {
                    t = n;
                    break;
                  }
                return t;
              }),
              (t.prototype.onClickDoubleUp = function () {
                var e = this;
                c.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: s.BuriedOneKey.luckyWheel,
                    actionName: s.BuriedTwoKey.victoryBtnClick,
                  }),
                  this.img_clock.node.stopAllActions(),
                  d.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                  this.scheduleOnce(function () {
                    c.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: s.BuriedPointKey.TurntableReward,
                        isDoubleUp: !0,
                        rewardCoins: 2 * e._rewardCoins,
                      }),
                      l.default.watchVideo(function () {
                        cc.director.emit(
                          s.GameEvent.Turntable_Show_Get_Reward,
                          2 * e._rewardCoins
                        ),
                          c.default
                            .getInstance()
                            .sendBuriedPointInfo({
                              event: s.BuriedOneKey.goldEarnCount,
                              value: 2 * e._rewardCoins,
                            }),
                          c.default
                            .getInstance()
                            .sendBuriedPointInfo({
                              event: s.BuriedOneKey.luckyWheel,
                              actionName: s.BuriedTwoKey.victoryResultShow,
                              value: 2,
                            }),
                          e.onClose();
                      }, s.ADType.TurntableDoubleUp);
                  }, 1);
              }),
              i([g(cc.Label)], t.prototype, "labRewardCoinsTop", void 0),
              i([g(cc.Label)], t.prototype, "labRewardCoinsBottom", void 0),
              i([g(cc.Button)], t.prototype, "btn_close", void 0),
              i([g(cc.Sprite)], t.prototype, "img_clock", void 0),
              i([g(cc.Label)], t.prototype, "label_clock_reward", void 0),
              i([g(cc.Label)], t.prototype, "label_txt", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/AudioManager": "AudioManager",
        "../../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Native/NativeBridge": "NativeBridge",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    RobotManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "30dfe0ARe9Iy4Xo3dOqC617", "RobotManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("../Utils/Utils"),
          r = e("./ChessManager"),
          s = e("./GameDataManager"),
          c = e("./LuckManager"),
          l = e("./MapGridManager"),
          u = e("./RoomInfoManager"),
          d = e("./UserInfoManager"),
          p = (function () {
            function e() {
              (this._gameDifficultyJson = null),
                (this._gameDifficultyJson = s.default
                  .getInstance()
                  .getTools()
                  .getGameDifficultyJson());
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.rollDiceByPoints = function (e) {
                var t = i.default.getRandomNum(1, 100);
                if (t >= 1 && t <= 10) return e;
                for (var n = [1, 2, 3, 4, 5, 6], o = 0; o < n.length; o++)
                  if (n[o] == e) {
                    n.splice(o);
                    break;
                  }
                return n[i.default.getRandomNum(1, 5) - 1];
              }),
              (e.prototype.getRobotDicePoints = function (e) {
                return u.default.getInstance().getGameDifficulty() ==
                  a.GameDifficulty.Hard
                  ? (this.getInRobotAttackRangeSteps(e),
                    c.default.getInstance().getDefaultDicePoints())
                  : c.default.getInstance().getDefaultDicePoints();
              }),
              (e.prototype.getInRobotAttackRangeSteps = function (e) {
                var t = [],
                  n = d.default.getInstance().getMyselfUserInfo(),
                  o = r.default
                    .getInstance()
                    .getInNormalLineChess(n.getPlayerIndex()),
                  a = r.default.getInstance().getInNormalLineChess(e);
                if (o.length > 0 && a.length > 0) {
                  for (var i = 0; i < a.length; i++)
                    for (var s = a[i], c = 0; c < o.length; c++) {
                      var l = o[c],
                        u = s.getDiffStepsToDestination(l);
                      if (u >= 1 && u <= 6) {
                        var p = l.getCurPosGrid(),
                          f = p.getAllChess();
                        l.hasProtectiveCover() ||
                          p.isSafe() ||
                          1 != f.length ||
                          t.push({ chess: l, diffSteps: u });
                      }
                    }
                  return t.length > 0
                    ? (t.sort(function (e, t) {
                        return (
                          e.chess.getDiffStepsToTerminal() -
                          t.chess.getDiffStepsToTerminal()
                        );
                      }),
                      t[0].diffSteps)
                    : null;
                }
                return null;
              }),
              (e.prototype.getCanArriveTerminalChess = function (e, t) {
                for (var n = [], o = 0; o < e.length; o++) {
                  var a = e[o];
                  a.canArriveTerminal(t) && n.push(a);
                }
                return n;
              }),
              (e.prototype.getCanEateOtherChess = function (e, t) {
                u.default.getInstance().getGameDifficulty();
                for (var n = [], o = [], a = 0; a < e.length; a++) {
                  var i = e[a],
                    r = i.canEateOther(t);
                  null != r && o.push({ me: i, beEaten: r });
                }
                return (
                  o.length > 0 &&
                    (o.sort(function (e, t) {
                      return (
                        e.beEaten.getDiffStepsToTerminal() -
                        t.beEaten.getDiffStepsToTerminal()
                      );
                    }),
                    n.push(o[0].me)),
                  n
                );
              }),
              (e.prototype.getCanArriveSafeGridChess = function (e, t) {
                for (var n = [], o = 0; o < e.length; o++) {
                  var a = e[o];
                  a.canWalkToSafeGrid(t) && n.push(a);
                }
                return n;
              }),
              (e.prototype.getCanArrivePropGridChess = function (e, t) {
                for (var n = [], o = 0; o < e.length; o++) {
                  var a = e[o];
                  a.canWalkToPropGrid(t) && n.push(a);
                }
                return n;
              }),
              (e.prototype.getDangerousStrategyChess = function (e, t, n) {
                for (var a = [], i = [], s = 0; s < e.length; s++)
                  e[s].isInNormalLine() && i.push(e[s]);
                i.sort(function (e, t) {
                  return (
                    e.getDiffStepsToTerminal() - t.getDiffStepsToTerminal()
                  );
                });
                var c = d.default.getInstance().getAllUser();
                for (s = 0; s < c.length; s++) {
                  var l = c[s];
                  if (l.getPlayerIndex() != n) {
                    var u = r.default
                      .getInstance()
                      .getInNormalLineChess(l.getPlayerIndex());
                    if (u.length > 0)
                      for (var p = 0; p < u.length; p++)
                        for (var f = u[p], h = 0; h < i.length; h++) {
                          var g = i[h],
                            m = g.getCurPosGrid();
                          if (
                            f.isInAttackRange(g) &&
                            !m.isSafe() &&
                            1 == m.getAllChess().length
                          ) {
                            var _ = g.getArriveGrid(t);
                            f.isInAttackRange(_) ||
                              (a.indexOf(g) == o.ARRAY_ELE_NOT_EXIST &&
                                a.push(g));
                          }
                        }
                  }
                }
                return a;
              }),
              (e.prototype.getNearestToTerminalChess = function (e) {
                var t = e.slice(0);
                return (
                  t.sort(function (e, t) {
                    return (
                      e.getDiffStepsToTerminal() - t.getDiffStepsToTerminal()
                    );
                  }),
                  t[0]
                );
              }),
              (e.prototype.walkByChessArray = function (e, t) {
                e.length > 0 &&
                  (1 == e.length
                    ? e[0].walk(t)
                    : this.getNearestToTerminalChess(e).walk(t));
              }),
              (e.prototype.getDefaultWalkChess = function (e, t) {
                for (var n = [], o = 0; o < e.length; o++)
                  e[o].canWalkToBombGrid(t) || n.push(e[o]);
                if (0 == n.length) for (o = 0; o < e.length; o++) n.push(e[o]);
                return n;
              }),
              (e.prototype.doDefaultStrategy = function (e, t) {
                var n = this.getDefaultWalkChess(e, t);
                n.length > 0
                  ? this.walkByChessArray(n, t)
                  : cc.log(
                      "Error, \u6682\u65f6\u6ca1\u6709\u53ef\u8d70\u7684\u68cb\u5b50\uff0c\u7b56\u7565\u51fa\u9519"
                    );
              }),
              (e.prototype.doChessWalkStrategy = function (e, t, n) {
                var o = this.getCanArriveTerminalChess(e, t);
                if (o.length > 0) this.walkByChessArray(o, t);
                else {
                  var a = this.getCanEateOtherChess(e, t);
                  if (a.length > 0) this.walkByChessArray(a, t);
                  else {
                    var i = this.getCanArriveSafeGridChess(e, t);
                    if (i.length > 0) this.walkByChessArray(i, t);
                    else {
                      var r = this.getCanArrivePropGridChess(e, t);
                      if (r.length > 0) this.walkByChessArray(r, t);
                      else if (this._gameDifficultyJson.dangerousAreaIsOpen) {
                        var s = this.getDangerousStrategyChess(e, t, n);
                        s.length > 0
                          ? this.walkByChessArray(s, t)
                          : this.doDefaultStrategy(e, t);
                      } else this.doDefaultStrategy(e, t);
                    }
                  }
                }
              }),
              (e.prototype.walk = function (e, t, n) {
                t == o.DICE_MAX_POINTS
                  ? this.sixPointsStrategy(e, t, n)
                  : this.doChessWalkStrategy(e, t, n);
              }),
              (e.prototype.sixPointsStrategy = function (e, t, n) {
                var o = [],
                  i = 0,
                  r = u.default.getInstance().getRoomMode();
                r == a.GameRoomMode.Quick
                  ? (i = this._gameDifficultyJson.sixPointsNotOutQuick)
                  : r == a.GameRoomMode.Classic &&
                    (i = this._gameDifficultyJson.sixPointsNotOutClassic);
                for (var s = 0; s < e.length; s++)
                  e[s].isAtTheBase() || o.push(e[s]);
                o.length >= i
                  ? this.doChessWalkStrategy(o, t, n)
                  : this.doChessWalkStrategy(e, t, n);
              }),
              (e.prototype.randomSendExpression = function (e) {
                if (
                  (void 0 === e && (e = !1),
                  u.default.getInstance().getGameMode() != a.GameMode.Local)
                ) {
                  var t = d.default.getInstance().getAllUser(),
                    n = [
                      "baiyan",
                      "chijing",
                      "daxiao",
                      "huachi",
                      "keai",
                      "liulei",
                      "shengqi",
                      "tule",
                    ],
                    o = i.default.getRandomNum(1, 10),
                    r = i.default.getRandomNum(1, 8);
                  if (2 == t.length) {
                    if (o <= 3) {
                      var s = {
                        playerIndex: t[1].getPlayerIndex(),
                        expressionName: n[r - 1],
                      };
                      cc.director.emit(a.GameEvent.send_Expression, s);
                    }
                  } else if (4 == t.length) {
                    var c = 0,
                      l = 0;
                    if ((e ? ((c = 1), (l = 2)) : ((c = 2), (l = 3)), o <= c)) {
                      var p = i.default.getRandomArrayElements([1, 2, 3], 2);
                      (s = { playerIndex: p[0], expressionName: n[r - 1] }),
                        cc.director.emit(a.GameEvent.send_Expression, s);
                      var f = i.default.getRandomNum(1, 8),
                        h = { playerIndex: p[1], expressionName: n[f - 1] };
                      cc.director.emit(a.GameEvent.twoRobat_Expression, h);
                    } else
                      o == l &&
                        ((s = {
                          playerIndex: i.default.getRandomNum(1, 3),
                          expressionName: n[r - 1],
                        }),
                        cc.director.emit(a.GameEvent.send_Expression, s));
                  }
                }
              }),
              (e.prototype.beEatSendExpression = function (e) {
                var t = i.default.getRandomNum(1, 10),
                  n = i.default.getRandomNum(1, 3);
                if (1 == i.default.getRandomNum(1, 2)) {
                  if (t <= 3) {
                    var o = {
                      playerIndex: e,
                      expressionName: ["shengqi", "liulei", "chijing"][n - 1],
                    };
                    cc.director.emit(a.GameEvent.send_Expression, o);
                  }
                } else
                  i.default.getRandomNum(1, 100) <= 30 &&
                    ((o = { playerIndex: e, expressionName: "chat_unlucky" }),
                    cc.director.emit(a.GameEvent.send_Sentence, o));
              }),
              (e.prototype.eatPlayChess = function (e) {
                var t = i.default.getRandomNum(1, 10),
                  n = i.default.getRandomNum(1, 3);
                if (1 == i.default.getRandomNum(1, 2)) {
                  if (t <= 2) {
                    var o = {
                      playerIndex: e,
                      expressionName: ["daxiao", "keai", "tule"][n - 1],
                    };
                    cc.director.emit(a.GameEvent.send_Expression, o);
                  }
                } else
                  i.default.getRandomNum(1, 100) <= 30 &&
                    ((o = { playerIndex: e, expressionName: "chat_hahaha" }),
                    cc.director.emit(a.GameEvent.send_Sentence, o));
              }),
              (e.prototype.playChessInVerticalLine = function () {
                if (u.default.getInstance().getGameMode() != a.GameMode.Local) {
                  var e = 0,
                    t = 0,
                    n = u.default.getInstance().getPlayerCount(),
                    o = d.default.getInstance().getAllUser();
                  if (
                    (u.default.getInstance().getRoomMode() ==
                    a.GameRoomMode.Quick
                      ? ((e = 4),
                        (t =
                          n == a.PlayerCount.Two
                            ? o[1].getPlayerIndex()
                            : i.default.getRandomNum(1, 3)))
                      : ((e = 2),
                        (t =
                          n == a.PlayerCount.Two
                            ? o[1].getPlayerIndex()
                            : i.default.getRandomNum(1, 3))),
                    1 == i.default.getRandomNum(1, 2))
                  ) {
                    var r = i.default.getRandomNum(1, 10),
                      s = i.default.getRandomNum(1, 3);
                    if (r <= e) {
                      var c = {
                        playerIndex: t,
                        expressionName: ["shengqi", "liulei", "chijing"][s - 1],
                      };
                      cc.director.emit(a.GameEvent.send_Expression, c);
                    }
                  } else
                    i.default.getRandomNum(1, 100) <= 30 &&
                      ((c = {
                        playerIndex: t,
                        expressionName: "chat_goodgame",
                      }),
                      cc.director.emit(a.GameEvent.send_Sentence, c));
                }
              }),
              (e.prototype.robotChessInVerticalLine = function (e) {
                if (u.default.getInstance().getGameMode() != a.GameMode.Local) {
                  var t;
                  if (
                    ((t =
                      u.default.getInstance().getRoomMode() ==
                      a.GameRoomMode.Quick
                        ? 4
                        : 2),
                    1 == i.default.getRandomNum(1, 2))
                  ) {
                    var n = i.default.getRandomNum(1, 10),
                      o = i.default.getRandomNum(1, 4);
                    if (n <= t) {
                      var r = {
                        playerIndex: e,
                        expressionName: ["daxiao", "keai", "huachi", "tule"][
                          o - 1
                        ],
                      };
                      cc.director.emit(a.GameEvent.send_Expression, r);
                    }
                  } else
                    i.default.getRandomNum(1, 100) <= 30 &&
                      ((r = {
                        playerIndex: e,
                        expressionName: "chat_goodgame",
                      }),
                      cc.director.emit(a.GameEvent.send_Sentence, r));
                }
              }),
              (e.prototype.randomSendSentence = function () {
                if (!(i.default.getRandomNum(1, 100) > 25)) {
                  var e = ["chat_hi", "chat_hello", "chat_goodluck"];
                  if (
                    u.default.getInstance().getRoomMode() ==
                    a.GameRoomMode.Quick
                  ) {
                    var t = {
                      playerIndex: 1,
                      expressionName: e[(n = i.default.getRandomNum(1, 3))],
                    };
                    cc.director.emit(a.GameEvent.send_Sentence, t);
                  } else {
                    var n = i.default.getRandomNum(1, 3);
                    (t = {
                      playerIndex: i.default.getRandomNum(1, 3),
                      expressionName: e[n],
                    }),
                      cc.director.emit(a.GameEvent.send_Sentence, t);
                  }
                }
              }),
              (e.prototype.robotReply = function (e) {
                switch (e) {
                  case "chat_hi":
                  case "chat_hello":
                    this.randomRobotSend(["chat_hi", "chat_hello"], 40);
                    break;
                  case "chat_goodluck":
                    this.randomRobotSend(
                      ["chat_goodluck", "chat_goodluck"],
                      40
                    );
                    break;
                  case "chat_oops":
                    this.randomRobotSend(["chijing", "tule"], 40, !0);
                    break;
                  case "chat_unlucky":
                    1 == i.default.getRandomNum(1, 2)
                      ? this.randomRobotSend(["liulei", "liulei"], 30, !0)
                      : this.randomRobotSend(["chat_hi", "chat_hi"], 30, !1);
                    break;
                  case "chat_nicemove":
                    1 == i.default.getRandomNum(1, 2)
                      ? this.randomRobotSend(["daxiao", "keai"], 30, !0)
                      : this.randomRobotSend(["chat_hi", "chat_hi"], 30, !1);
                    break;
                  case "chat_goodgame":
                    this.randomRobotSend(
                      ["chat_goodluck", "chat_goodluck"],
                      45
                    );
                    break;
                  case "chat_wellplayed":
                    this.randomRobotSend(["daxiao", "keai", "huachi"], 30, !0);
                    break;
                  case "chat_playfast":
                    this.randomRobotSend(["baiyan", "keai"], 30, !0);
                    break;
                  case "chat_iwilleatyou":
                    this.randomRobotSend(["shengqi", "liulei"], 30, !0);
                    break;
                  case "chat_plzdontkill":
                    1 == i.default.getRandomNum(1, 2)
                      ? this.randomRobotSend(["daxiao", "daxiao"], 30, !0)
                      : this.randomRobotSend(
                          ["chat_hahaha", "chat_unlucky"],
                          30,
                          !1
                        );
                    break;
                  case "chat_hahaha":
                    this.randomRobotSend(["daxiao", "daxiao"], 30, !0);
                }
              }),
              (e.prototype.robotSendExpressionAndSentence = function (e, t, n) {
                if (i.default.getRandomNum(1, 100) <= n) {
                  var o = {
                    playerIndex: t[i.default.getRandomNum(1, t.length) - 1],
                    expressionName: e[i.default.getRandomNum(1, e.length) - 1],
                  };
                  cc.director.emit(a.GameEvent.send_Expression, o);
                }
              }),
              (e.prototype.randomRobotSend = function (e, t, n) {
                void 0 === n && (n = !1),
                  n
                    ? u.default.getInstance().getRoomMode() ==
                      a.GameRoomMode.Quick
                      ? this.robotSendExpressionAndSentence(e, [1, 1], t)
                      : this.robotSendExpressionAndSentence(e, [1, 2, 3], t)
                    : u.default.getInstance().getRoomMode() ==
                      a.GameRoomMode.Quick
                    ? this.robotSendSentence(e, [1, 1], t)
                    : this.robotSendSentence(e, [1, 2, 3], t);
              }),
              (e.prototype.robotSendSentence = function (e, t, n) {
                if (i.default.getRandomNum(1, 100) <= n) {
                  var o = {
                    playerIndex: t[i.default.getRandomNum(1, t.length) - 1],
                    expressionName: e[i.default.getRandomNum(1, e.length) - 1],
                  };
                  cc.director.emit(a.GameEvent.send_Sentence, o);
                }
              }),
              (e.prototype.robatBomb = function (e) {
                var t = [],
                  n = s.default.getInstance().getBomb(e);
                console.log("bombCount: " + n);
                for (
                  var o = s.default.getInstance().getTools().getMapInfoJson(),
                    r = [],
                    c = 0;
                  c < o.colorGrids.length;
                  c++
                )
                  for (var u = o.colorGrids[c], d = 0; d < u.length; d++)
                    r.push(u[d]);
                if (n < 3 && i.default.getRandomNum(1, 100) <= 30) {
                  var p = l.default.getInstance().getAllMapGrid();
                  for (c = 0; c < p.length; c++) {
                    var f = p[c];
                    0 == f.isSafe() &&
                      0 == f.hasBomb() &&
                      0 == f.getIsHaveChess() &&
                      -1 == r.indexOf(f.getGridIndex()) &&
                      t.push(f.getGridIndex());
                  }
                  console.log("canBombMapIndexList: " + t);
                  var h = i.default.getRandomArrayElements(t, 1);
                  console.log("bombList: " + h[0]),
                    cc.director.emit(a.GameEvent.ShowBomb, h[0]),
                    s.default.getInstance().setBombInfo(e);
                }
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = p), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Utils/Utils": "Utils",
        "./ChessManager": "ChessManager",
        "./GameDataManager": "GameDataManager",
        "./LuckManager": "LuckManager",
        "./MapGridManager": "MapGridManager",
        "./RoomInfoManager": "RoomInfoManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    RoomInfoManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "febc42X6G5Gs75ykQqgxpiU", "RoomInfoManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameEnum"),
          a = e("./GameDataManager"),
          i = e("./UserInfoManager"),
          r = (function () {
            function e() {
              (this._gameMode = o.GameMode.Online),
                (this._computerMode = o.GameRoomMode.Quick),
                (this._roomMode = o.GameRoomMode.Quick),
                (this._chessColor = o.ChessColor.Blue),
                (this._onlineChessColor = o.ChessColor.Blue),
                (this._computerChessColor = o.ChessColor.Blue),
                (this._onlinePlayerCount = o.PlayerCount.Four),
                (this._computerPlayerCount = o.PlayerCount.Four),
                (this._playerCount = o.PlayerCount.Four),
                (this._entryGold = 0),
                (this._pumpingRatio = 0.05),
                (this._playerWinGold = { first: 0, second: 0 }),
                (this._mapType = o.MapType.Four),
                (this._playerGetExp = { winExp: 0, lostExp: 0 }),
                (this._isOverTime = !1),
                (this._entranceType = o.Entrance.Room),
                this.loadGameMode();
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.loadGameMode = function () {
                var e = a.default.getInstance().getTools().getGameInfoJson(),
                  t = e.info[0].online_player_count,
                  n = e.info[0].online_game_mode,
                  o = e.info[0].computer_player_count,
                  i = e.info[0].computer_game_mode;
                this.setOnlinePlayerCount(t),
                  this.setRoomMode(n),
                  this.setComputerPlayerCount(o),
                  this.setComputerRoomMode(i);
              }),
              (e.prototype.setGameMode = function (e) {
                this._gameMode = e;
              }),
              (e.prototype.getGameMode = function () {
                return this._gameMode;
              }),
              (e.prototype.setRoomMode = function (e) {
                this._roomMode = e;
              }),
              (e.prototype.getRoomMode = function () {
                return this._roomMode;
              }),
              (e.prototype.setComputerRoomMode = function (e) {
                this._computerMode = e;
              }),
              (e.prototype.getComputerRoomMode = function () {
                return this._computerMode;
              }),
              (e.prototype.setChessColor = function (e) {
                this._chessColor = e;
              }),
              (e.prototype.getChessColor = function () {
                return this._chessColor;
              }),
              (e.prototype.setOnlineChessColor = function (e) {
                this._onlineChessColor = e;
              }),
              (e.prototype.getOnlineChessColor = function () {
                return this._onlineChessColor;
              }),
              (e.prototype.setComputerChessColor = function (e) {
                this._computerChessColor = e;
              }),
              (e.prototype.getComputerChessColor = function () {
                return this._computerChessColor;
              }),
              (e.prototype.setPlayerCount = function (e) {
                this._playerCount = e;
              }),
              (e.prototype.getPlayerCount = function () {
                return this._playerCount;
              }),
              (e.prototype.setOnlinePlayerCount = function (e) {
                this._onlinePlayerCount = e;
              }),
              (e.prototype.getOnlinePlayerCount = function () {
                return this._onlinePlayerCount;
              }),
              (e.prototype.setComputerPlayerCount = function (e) {
                this._computerPlayerCount = e;
              }),
              (e.prototype.getComputerPlayerCount = function () {
                return this._computerPlayerCount;
              }),
              (e.prototype.setEntryGold = function (e) {
                this._entryGold = e;
              }),
              (e.prototype.getEntryGold = function () {
                return this._entryGold;
              }),
              (e.prototype.caculatePlayerWinGold = function () {
                if (
                  this._roomMode == o.GameRoomMode.Quick ||
                  (this._roomMode == o.GameRoomMode.Classic &&
                    this._playerCount == o.PlayerCount.Two)
                )
                  (this._playerWinGold.first =
                    this._entryGold *
                    this._playerCount *
                    (1 - this._pumpingRatio)),
                    (this._playerWinGold.second = 0);
                else {
                  var e = this._entryGold * this._playerCount;
                  (this._playerWinGold.first =
                    0.75 * e - e * this._pumpingRatio),
                    (this._playerWinGold.second = 0.25 * e);
                }
                return this._playerWinGold;
              }),
              (e.prototype.getPlayerWinGold = function () {
                return this._playerWinGold;
              }),
              (e.prototype.setMapType = function (e) {
                this._mapType = e;
              }),
              (e.prototype.getMapType = function () {
                return this._mapType;
              }),
              (e.prototype.setPlayerGetExp = function () {}),
              (e.prototype.getPlayerGetExp = function () {
                for (
                  var e = a.default
                      .getInstance()
                      .getTools()
                      .getEntryCoinsJson(),
                    t = 0;
                  t < e.infos.length;
                  t++
                )
                  if (e.infos[t].coins == this._entryGold) {
                    (this._playerGetExp.winExp = e.infos[t].winExp),
                      (this._playerGetExp.lostExp = e.infos[t].lostExp);
                    break;
                  }
                return this._playerGetExp;
              }),
              (e.prototype.matchGameDifficulty = function () {
                var e = i.default.getInstance().getContinueResult();
                if (e) {
                  var t = e.result,
                    n = e.continueCount;
                  this.getGameDifficulty() == o.GameDifficulty.Esay
                    ? t == o.GameResult.Success &&
                      n >= 1 &&
                      (this.setGameDifficulty(o.GameDifficulty.Normal),
                      i.default.getInstance().clearResultHistories())
                    : this.getGameDifficulty() == o.GameDifficulty.Normal
                    ? t == o.GameResult.Success && n >= 2
                      ? (this.setGameDifficulty(o.GameDifficulty.Hard),
                        i.default.getInstance().clearResultHistories())
                      : t == o.GameResult.Fail &&
                        n >= 2 &&
                        (this.setGameDifficulty(o.GameDifficulty.Esay),
                        i.default.getInstance().clearResultHistories())
                    : this.getGameDifficulty() == o.GameDifficulty.Hard &&
                      t == o.GameResult.Fail &&
                      n >= 1 &&
                      (this.setGameDifficulty(o.GameDifficulty.Normal),
                      i.default.getInstance().clearResultHistories());
                }
              }),
              (e.prototype.setGameDifficulty = function (e) {
                i.default.getInstance().setGameDifficultyInfo(e, null);
              }),
              (e.prototype.getGameDifficulty = function () {
                return i.default.getInstance().getGameDifficultyInfo()
                  .gameDifficulty;
              }),
              (e.prototype.setIsOverTime = function (e) {
                this._isOverTime = e;
              }),
              (e.prototype.getIsOverTime = function () {
                return this._isOverTime;
              }),
              (e.prototype.setEntranceType = function (e) {
                this._entranceType = e;
              }),
              (e.prototype.getEntranceType = function () {
                return this._entranceType;
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = r), cc._RF.pop();
      },
      {
        "../Enum/GameEnum": "GameEnum",
        "./GameDataManager": "GameDataManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    SettlementItem: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "714b5e3yedCRpMYtEEWd2rg", "SettlementItem");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = cc._decorator,
          l = c.ccclass,
          u = c.property,
          d = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprHeadPhoto = null),
                (t.nodeWin = null),
                (t.nodeLost = null),
                (t.sprBg = null),
                (t.spfWinBgs = []),
                (t.spfLostBgs = []),
                (t.sprHuangGuan = null),
                (t.labNickName = null),
                (t.labGold = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.start = function () {}),
              (t.prototype.setInfoWin = function (e, t, n, o) {
                var a = this;
                (this.labNickName.string = t.getNickName()),
                  this.loadRes(
                    s.PLAYER_HEAD_PHOTO_PATH +
                      "img_head_photo_" +
                      t.getHeadPhotoIdx(),
                    cc.SpriteFrame,
                    function (e) {
                      a.sprHeadPhoto.spriteFrame = e;
                    }
                  ),
                  (this.sprHuangGuan.active = 0 == e),
                  n
                    ? ((this.nodeWin.active = !0),
                      (this.nodeLost.active = !1),
                      (this.sprBg.spriteFrame = this.spfWinBgs[0]),
                      (this.labGold.string = "+" + o))
                    : ((this.nodeWin.active = !1),
                      (this.nodeLost.active = !0),
                      (this.sprBg.spriteFrame = this.spfWinBgs[1]));
              }),
              (t.prototype.setInfoLost = function (e, t, n, o) {
                var a = this;
                (this.labNickName.string = t.getNickName()),
                  this.loadRes(
                    s.PLAYER_HEAD_PHOTO_PATH +
                      "img_head_photo_" +
                      t.getHeadPhotoIdx(),
                    cc.SpriteFrame,
                    function (e) {
                      a.sprHeadPhoto.spriteFrame = e;
                    }
                  ),
                  (this.sprHuangGuan.active = 0 == e),
                  n
                    ? ((this.nodeWin.active = !0),
                      (this.nodeLost.active = !1),
                      (this.sprBg.spriteFrame = this.spfLostBgs[0]),
                      (this.labGold.string = "+" + o))
                    : ((this.nodeWin.active = !1),
                      (this.nodeLost.active = !0),
                      t.isMyself()
                        ? (this.sprBg.spriteFrame = this.spfLostBgs[2])
                        : (this.sprBg.spriteFrame = this.spfLostBgs[1]));
              }),
              i([u(cc.Sprite)], t.prototype, "sprHeadPhoto", void 0),
              i([u(cc.Node)], t.prototype, "nodeWin", void 0),
              i([u(cc.Node)], t.prototype, "nodeLost", void 0),
              i([u(cc.Sprite)], t.prototype, "sprBg", void 0),
              i([u(cc.SpriteFrame)], t.prototype, "spfWinBgs", void 0),
              i([u(cc.SpriteFrame)], t.prototype, "spfLostBgs", void 0),
              i([u(cc.Node)], t.prototype, "sprHuangGuan", void 0),
              i([u(cc.Label)], t.prototype, "labNickName", void 0),
              i([u(cc.Label)], t.prototype, "labGold", void 0),
              i([l], t)
            );
          })(r.default);
        (n.default = d), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
      },
    ],
    ShopDataManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "46b49xH8tZGDJ8xSPKZNuku", "ShopDataManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameEnum"),
          a = e("../Native/NativeBridge"),
          i = e("../Utils/Utils"),
          r = e("./GameDataManager"),
          s = e("./UserInfoManager"),
          c = (function () {
            function e() {
              (this._shopJson = null),
                (this._shopDatas = []),
                (this._skinJson = null),
                (this._skinDatas = []),
                (this._vasShopDatas = []),
                (this._selectToken = "original"),
                (this._selectBoard = "original"),
                (this._selectDice = "original"),
                (this._debris = []),
                this.initShopData();
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.getShopTypeInfoByProductId = function (e) {
                for (var t = 0; t < this._shopJson.golds.length; t++)
                  if ((n = this._shopJson.golds[t]).productId == e)
                    return { type: o.ShopShowType.Gold, info: n };
                for (t = 0; t < this._shopJson.diamond.length; t++)
                  if ((n = this._shopJson.diamond[t]).productId == e)
                    return { type: o.ShopShowType.Dimaond, info: n };
                for (t = 0; t < this._shopJson.skin.length; t++) {
                  var n;
                  if ((n = this._shopJson.skin[t]).productId == e)
                    return { type: o.ShopShowType.Skin, info: n };
                }
              }),
              (e.prototype.initShopData = function () {
                (this._shopDatas[o.ShopShowType.Gold] = []),
                  (this._shopDatas[o.ShopShowType.Dimaond] = []),
                  (this._shopDatas[o.ShopShowType.Skin] = []),
                  s.default.getInstance().loadGoodsInfo(),
                  (this._shopJson = r.default
                    .getInstance()
                    .getTools()
                    .getShopJson()),
                  (this._skinJson = r.default
                    .getInstance()
                    .getTools()
                    .getShopSkinJson());
                var e = s.default.getInstance().getGoodsInfo(),
                  t = s.default.getInstance().getVasShopInfo(),
                  n = a.default.getData(o.DataSaveKey.Select_Token);
                n && (this._selectToken = JSON.parse(n));
                var i = a.default.getData(o.DataSaveKey.Select_Dice);
                i && (this._selectDice = JSON.parse(i));
                var c = a.default.getData(o.DataSaveKey.Select_Board);
                if (
                  (c && (this._selectBoard = JSON.parse(c)),
                  null != e && null != e)
                ) {
                  for (var l = 0; l < e.length; l++) {
                    if ((a.default.nativeLog("GPShopInfo: " + e[l]), e[l].b)) {
                      var u = e[l].b.nameValuePairs,
                        d = this.getShopTypeInfoByProductId(u.productId);
                      d &&
                        this._shopDatas[d.type].push({
                          product: u,
                          info: d.info,
                        });
                    }
                    this._shopDatas[o.ShopShowType.Gold].length > 0 &&
                      (this._shopDatas[o.ShopShowType.Gold].sort(function (
                        e,
                        t
                      ) {
                        return (
                          e.product.price_amount_micros -
                          t.product.price_amount_micros
                        );
                      }),
                      a.default.nativeLog(
                        "this._shopDatas[ShopShowType.Gold]: " +
                          this._shopDatas[o.ShopShowType.Gold]
                      )),
                      this._shopDatas[o.ShopShowType.Dimaond].length > 0 &&
                        (this._shopDatas[o.ShopShowType.Dimaond].sort(function (
                          e,
                          t
                        ) {
                          return (
                            e.product.price_amount_micros -
                            t.product.price_amount_micros
                          );
                        }),
                        a.default.nativeLog(
                          "this._shopDatas[ShopShowType.Dimaond]: " +
                            this._shopDatas[o.ShopShowType.Dimaond]
                        ));
                  }
                  for (l = 0; l < t.length; l++) {
                    var p = t[l];
                    p && this._vasShopDatas.push(p);
                  }
                  this.checkSkinOverdue();
                }
              }),
              (e.prototype.checkSkinOverdue = function () {
                var e = s.default.getInstance().getShopSkinList();
                for (var t in e)
                  switch (this.getSkinInfo(e[t].id).type) {
                    case o.SkinType.Token:
                      e[t].endTime < i.default.getCurTimeStamp() &&
                        (this._selectToken = "original");
                      break;
                    case o.SkinType.Board:
                      e[t].endTime < i.default.getCurTimeStamp() &&
                        (this._selectBoard = "original");
                      break;
                    case o.SkinType.Dice:
                      e[t].endTime < i.default.getCurTimeStamp() &&
                        (this._selectDice = "original");
                  }
              }),
              (e.prototype.getShopData = function (e) {
                return this._shopDatas[e];
              }),
              (e.prototype.getVASShopData = function () {
                return this._vasShopDatas;
              }),
              (e.prototype.getSkinShopDataBySkinName = function (e) {
                var t = this.getShopData(o.ShopShowType.Skin);
                if (t)
                  for (var n = 0; n < t.length; n++)
                    if (t[n].info.skinName == e) return t[n];
              }),
              (e.prototype.getSkinList = function (e) {
                var t = this._skinJson.info,
                  n = [];
                for (var o in t) t[o].type == e && n.push(t[o]);
                return n;
              }),
              (e.prototype.getSkinInfo = function (e) {
                var t = this._skinJson.info,
                  n = null;
                for (var o in t)
                  if (t[o].id == e) {
                    n = t[o];
                    break;
                  }
                return n;
              }),
              (e.prototype.setSelectToken = function (e) {
                (this._selectToken = e),
                  a.default.saveData(
                    o.DataSaveKey.Select_Token,
                    JSON.stringify(e)
                  );
              }),
              (e.prototype.getSelectToken = function () {
                return this._selectToken;
              }),
              (e.prototype.setSelectBoard = function (e) {
                (this._selectBoard = e),
                  a.default.saveData(
                    o.DataSaveKey.Select_Board,
                    JSON.stringify(e)
                  );
              }),
              (e.prototype.getSelectBoard = function () {
                return this._selectBoard;
              }),
              (e.prototype.setSelectDice = function (e) {
                (this._selectDice = e),
                  a.default.saveData(
                    o.DataSaveKey.Select_Dice,
                    JSON.stringify(e)
                  );
              }),
              (e.prototype.getSelectDice = function () {
                return this._selectDice;
              }),
              (e.prototype.getDebrisIDList = function (e) {
                var t = this._skinJson.info,
                  n = [];
                for (var a in t)
                  t[a].getType == o.SkinGetType.debris &&
                    e == t[a].id &&
                    n.push(t[a]);
                return n;
              }),
              (e.prototype.isHaveDebris = function (e) {
                return -1 != this._debris.indexOf(e);
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = c), cc._RF.pop();
      },
      {
        "../Enum/GameEnum": "GameEnum",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
        "./GameDataManager": "GameDataManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    SignView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "c9cdaq1AG1FDqsxmExVdm6f", "SignView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/GameDataManager"),
          d = e("../Framework/Manager/UserInfoManager"),
          p = e("../Framework/Native/NativeBridge"),
          f = e("../Framework/Utils/Utils"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.nodeDays = []),
                (t.img_clock = null),
                (t.label_txt = []),
                (t.node_cannel = null),
                (t._todaySignData = null),
                (t.clockList = [
                  -223, -133, -133, -45, -45, 45, 45, 133, 133, 223,
                ]),
                (t.clockMultiple = [3, 2, 5, 2, 3]),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                f.default.localStr(this.node),
                  d.default.getInstance().isShowAppluck(!1),
                  p.default.preloadReward(s.ADType.SignDoubleUp),
                  p.default.preInterstitialReady(s.ADType.SignReward),
                  d.default.getInstance().getSignInfo(),
                  this.updateUI();
                for (var e = 0; e < this.clockMultiple.length; e++)
                  this.label_txt[e].string = "x" + this.clockMultiple[e];
              }),
              (t.prototype.updateUI = function () {
                for (
                  var e = d.default.getInstance().getSignData(),
                    t = d.default.getInstance().getSignInfo(),
                    n = 0;
                  n < e.length;
                  n++
                )
                  this.setDayItem(e[n].dayIndex, e[n].status, e[n].coins),
                    e[n].status == s.RewardStatus.Can &&
                      (this._todaySignData = e[n]);
                this.node_cannel.active = t.isAd;
              }),
              (t.prototype.onClickClose = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = d.default.getInstance().getSignInfo();
                if (
                  (cc.director.emit(s.GameEvent.Close_Parent_Ui), e.isSignToday)
                )
                  return (
                    this.onClose(),
                    void d.default.getInstance().isShowAppluck(!0)
                  );
                l.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: s.BuriedPointKey.Sign,
                    signDay: e.continueDayIdx + 1,
                    isDoubleUp: !1,
                  }),
                  p.default.watchVideo(function () {}, "signview_Insert"),
                  this.getReward(1, !1, !0);
              }),
              (t.prototype.onClickGet = function () {
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var e = d.default.getInstance().getSignInfo();
                e.isSignToday
                  ? this.onClose()
                  : (l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: s.BuriedPointKey.Sign,
                        signDay: e.continueDayIdx + 1,
                        isDoubleUp: !1,
                      }),
                    this.getReward(1, !1, !1),
                    this.updateUI());
              }),
              (t.prototype.onClickDoubleUp = function () {
                var e = this;
                if (
                  (c.default
                    .getInstance()
                    .playEffectWithPath(s.AudioType.Button_Click),
                  u.default.getInstance().getTools().showNoNetWorkTip())
                ) {
                  var t = d.default.getInstance().getSignInfo();
                  if (t.isAd) return;
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedOneKey.sign,
                      actionName: s.BuriedTwoKey.isDoubleUp,
                      value: 1,
                    }),
                    l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: s.BuriedOneKey.sign,
                        actionName: s.BuriedTwoKey.signDay,
                        value: t.continueDayIdx + 1,
                      }),
                    p.default.watchVideo(function () {
                      d.default.getInstance().addWatchADCount(),
                        t.isSignToday
                          ? e.getReward(1, !0, !0)
                          : e.getReward(2, !0, !0);
                    }, s.ADType.SignDoubleUp);
                }
              }),
              (t.prototype.update = function () {}),
              (t.prototype.getClockRewardDouble = function () {
                for (
                  var e = this.img_clock.node.x, t = 0, n = 0;
                  n < this.clockList.length / 2;
                  n++
                )
                  if (
                    this.clockList[2 * n] <= e &&
                    this.clockList[2 * n + 1] >= e
                  ) {
                    t = n;
                    break;
                  }
                return t;
              }),
              (t.prototype.getReward = function (e, t, n) {
                var o = d.default.getInstance().getSignData(),
                  a = d.default.getInstance().getSignInfo(),
                  i = a.continueDayIdx,
                  r = i;
                a.isSignToday && !a.isAd && (r -= 1);
                var c = o[r].coins;
                (c *= e),
                  a.isSignToday || (i += 1),
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedOneKey.goldEarnCount,
                      actionName: s.BuriedTwoKey.goldEarnCheckIn,
                      value: c,
                    }),
                  d.default
                    .getInstance()
                    .setSignInfo(f.default.getDateString(), i, !0, t),
                  n && this.onClose();
                var p = u.default.getInstance().getHallGoldPos();
                u.default
                  .getInstance()
                  .getTools()
                  .playFlyEffect(s.FlyEffectType.Coins, p, c, function () {
                    var e = d.default.getInstance().getMyselfUserInfo();
                    e.setGoldNum(e.getGoldNum() + c),
                      u.default.getInstance().isFirstEnterGame();
                  });
              }),
              (t.prototype.setDayItem = function (e, t) {
                var n = this.nodeDays[e],
                  o = n.getChildByName("sprRewardStatus"),
                  a = n.getChildByName("img_mask"),
                  i = n.getChildByName("sprDayBg"),
                  r = n.getChildByName("labDay"),
                  c = "img_get_sign_reward",
                  l = cc.color(21, 140, 210);
                e < 6
                  ? (t == s.RewardStatus.Got
                      ? ((a.active = !0), (c = "img_no_sign_reward"))
                      : t == s.RewardStatus.Can
                      ? ((a.active = !1),
                        (c = "img_get_sign_reward"),
                        (l = cc.color(154, 16, 189)))
                      : ((a.active = !1), (c = "img_no_sign_reward")),
                    this.loadRes(c, cc.SpriteFrame, function (e) {
                      i.getComponent(cc.Sprite).spriteFrame = e;
                    }))
                  : t == s.RewardStatus.Got
                  ? ((a.active = !0), (l = cc.color(193, 100, 0)))
                  : t == s.RewardStatus.Can
                  ? ((a.active = !1), (l = cc.color(154, 16, 189)))
                  : ((a.active = !1), (l = cc.color(193, 100, 0))),
                  (r.getComponent(cc.LabelOutline).color = l),
                  (o.active = t == s.RewardStatus.Got);
              }),
              i([m(cc.Node)], t.prototype, "nodeDays", void 0),
              i([m(cc.Sprite)], t.prototype, "img_clock", void 0),
              i([m(cc.Label)], t.prototype, "label_txt", void 0),
              i([m(cc.Node)], t.prototype, "node_cannel", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    StrategyManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "1d610YNjtNJDof92fInaslP", "StrategyManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = (function () {
          function e() {}
          return (
            (e.getInstance = function () {
              return e._instance || (e._instance = new e()), e._instance;
            }),
            (e._instance = null),
            e
          );
        })();
        (n.default = o), cc._RF.pop();
      },
      {},
    ],
    TaskManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "e03b2IHFVdKFoIZZA3rGcRW", "TaskManager"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameEnum"),
          a = e("../Native/NativeBridge"),
          i = e("../Utils/Utils"),
          r = e("./GameDataManager"),
          s = e("./UserInfoManager"),
          c = e("../Enum/GameConst"),
          l = (function () {
            function e() {
              (this._taskInfo = {}), (this._onlineRewardInfo = {});
            }
            return (
              (e.getInstance = function () {
                return e._instance || (e._instance = new e()), e._instance;
              }),
              (e.prototype.initTask = function () {
                var e = a.default.getData(o.DataSaveKey.Offline_Time_Info),
                  t = i.default.getDateString();
                if (i.default.getDiffDay(e, t))
                  s.default.getInstance().setOnlineTime(0),
                    this.initData(),
                    this.initOnlineReward(),
                    this.initIsEnterGame(),
                    this.initGetGoldCount();
                else {
                  var n = a.default.getData(o.DataSaveKey.Online_Time_Info),
                    r = "" != n ? parseInt(n) : 0;
                  s.default.getInstance().setOnlineTime(r);
                  var c = a.default.getData(o.DataSaveKey.Task_Info);
                  if ("" != c) {
                    var l = JSON.parse(c);
                    for (var u in l) this._taskInfo[l[u].data.id] = l[u];
                  } else this.initData();
                  var d = a.default.getData(o.DataSaveKey.Online_Reward_Info);
                  if ("" != d) {
                    var p = JSON.parse(d);
                    for (var u in p) this._onlineRewardInfo[p[u].id] = p[u];
                  } else this.initOnlineReward();
                }
              }),
              (e.prototype.initOnlineReward = function () {
                var e = r.default.getInstance().getTools().getOnlineJson();
                for (var t in e.info)
                  e.info[t].taskStatus ||
                    (e.info[t].taskStatus = o.TaskStatus.Task_NotCan),
                    (this._onlineRewardInfo[e.info[t].id] = e.info[t]);
                a.default.saveData(
                  o.DataSaveKey.Online_Reward_Info,
                  JSON.stringify(this._onlineRewardInfo)
                );
              }),
              (e.prototype.initIsEnterGame = function () {
                s.default.getInstance().setIsEnterGame(0);
              }),
              (e.prototype.initGetGoldCount = function () {
                s.default.getInstance().setGoldCount();
              }),
              (e.prototype.getOnlineRewardInfo = function () {
                return this._onlineRewardInfo;
              }),
              (e.prototype.setOnlineReward = function (e, t) {
                for (var n = 1; n <= e; n++)
                  this._onlineRewardInfo[n] &&
                    (this._onlineRewardInfo[n].taskStatus = t);
                a.default.saveData(
                  o.DataSaveKey.Online_Reward_Info,
                  JSON.stringify(this._onlineRewardInfo)
                ),
                  cc.director.emit(o.GameEvent.Update_Online_Reward);
              }),
              (e.prototype.initData = function () {
                for (var e = 0; e < c.TASK_JIN_NUM; e++) {
                  var t = this.getTaskInfo(o.TaskQuality.Task_yellow);
                  this._taskInfo[t.data.id] = t;
                }
                for (e = 0; e < c.TASK_LAN_NUM; e++)
                  (t = this.getTaskInfo(o.TaskQuality.Task_blue)),
                    this.isSame(t.data.id)
                      ? e--
                      : (this._taskInfo[t.data.id] = t);
                a.default.saveData(
                  o.DataSaveKey.Task_Info,
                  JSON.stringify(this._taskInfo)
                );
              }),
              (e.prototype.isSame = function (e) {
                for (var t in this._taskInfo)
                  if (this._taskInfo[t].data.id == e) return !0;
                return !1;
              }),
              (e.prototype.getTaskInfo = function (e) {
                var t = r.default.getInstance().getTools().getTaskJson(),
                  n = [],
                  a = {
                    data: null,
                    rewardType: 1,
                    rewardCount: 1,
                    complete: 0,
                    taskStatus: 2,
                    randomdice: 0,
                  };
                for (var s in t.info) t.info[s].qua == e && n.push(t.info[s]);
                var l = i.default.getRandomNum(0, n.length - 1);
                return (
                  (a.data = n[l]),
                  n[l].type == o.TaskType.Task_dice &&
                    (a.randomdice = i.default.getRandomNum(1, 6)),
                  e == o.TaskQuality.Task_yellow
                    ? (l = i.default.getRandomNum(0, 9)) > c.TASK_REWARD_RANDOM
                      ? (a.rewardType = o.GoldType.Skin_Experience)
                      : ((a.rewardType = o.GoldType.Diamonds),
                        (a.rewardCount = 30))
                    : ((a.rewardType = o.GoldType.Gold),
                      (a.rewardCount = n[l].reward),
                      console.log(
                        "taskInfo: " + n[l] + "reward: " + n[l].reward
                      )),
                  a
                );
              }),
              (e.prototype.getTask = function () {
                return this._taskInfo;
              }),
              (e.prototype.setTaskProgress = function (e, t) {
                for (var n in (void 0 === t && (t = 0), this._taskInfo))
                  this._taskInfo[n].data.type == e &&
                    (e == o.TaskType.Task_dice
                      ? this._taskInfo[n].randomdice == t &&
                        this._taskInfo[n].complete++
                      : this._taskInfo[n].complete++,
                    a.default.saveData(
                      o.DataSaveKey.Task_Info,
                      JSON.stringify(this._taskInfo)
                    ));
              }),
              (e.prototype.getTaskReward = function (e) {
                for (var t in this._taskInfo)
                  this._taskInfo[t].data.id == e &&
                    ((this._taskInfo[t].taskStatus = o.TaskStatus.Task_Got),
                    a.default.saveData(
                      o.DataSaveKey.Task_Info,
                      JSON.stringify(this._taskInfo)
                    ));
              }),
              (e._instance = null),
              e
            );
          })();
        (n.default = l), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
        "./GameDataManager": "GameDataManager",
        "./UserInfoManager": "UserInfoManager",
      },
    ],
    TimingBoxDealsItem: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "416ee5RGKxGH7+7MZfd0cji", "TimingBoxDealsItem");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/BuriedPointManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Native/NativeBridge"),
          p = cc._decorator,
          f = p.ccclass,
          h = p.property,
          g = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprCover = null),
                (t.sprLock = null),
                (t.btnCollect = null),
                (t.labText = null),
                (t.labCoinsAdd = null),
                (t.spfCoins = []),
                (t._curIndex = 0),
                (t._coinsAdd = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.start = function () {}),
              (t.prototype.setInfo = function (e, t, n, o, a) {
                (this._curIndex = e),
                  (this._coinsAdd = n),
                  (this.labCoinsAdd.string = "+" + n),
                  t == s.RewardStatus.NotCan
                    ? (this.labText.string = o + "/" + a)
                    : t == s.RewardStatus.Got
                    ? ((this.sprCover.active = !1),
                      (this.sprLock.active = !1),
                      (this.labText.string = "Collected"),
                      (this.btnCollect.interactable = !1))
                    : t == s.RewardStatus.Can &&
                      ((this.sprCover.active = !1),
                      (this.sprLock.active = !1),
                      (this.labText.string = "Collect"));
              }),
              (t.prototype.onClickCollect = function () {
                var e = this;
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click);
                var t = 0;
                0 == this._curIndex
                  ? (t = s.TimingBoxRewardType.CountReward1)
                  : 1 == this._curIndex
                  ? (t = s.TimingBoxRewardType.CountReward2)
                  : 2 == this._curIndex &&
                    (t = s.TimingBoxRewardType.CountReward3),
                  l.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedPointKey.TimingBox,
                      rewardType: t,
                      reward: this._coinsAdd,
                    }),
                  d.default.watchVideo(function () {
                    0 == e._curIndex
                      ? u.default
                          .getInstance()
                          .setTimingBoxInfo(
                            null,
                            null,
                            null,
                            null,
                            s.RewardStatus.Got,
                            null,
                            null
                          )
                      : 1 == e._curIndex
                      ? u.default
                          .getInstance()
                          .setTimingBoxInfo(
                            null,
                            null,
                            null,
                            null,
                            null,
                            s.RewardStatus.Got,
                            null
                          )
                      : 2 == e._curIndex &&
                        u.default
                          .getInstance()
                          .setTimingBoxInfo(
                            null,
                            null,
                            null,
                            null,
                            null,
                            null,
                            s.RewardStatus.Got
                          );
                    var t = u.default.getInstance().getMyselfUserInfo();
                    l.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: s.BuriedOneKey.goldEarnCount,
                        actionName: s.BuriedTwoKey.goldEarnReward,
                        value: e._coinsAdd,
                      }),
                      t.setGoldNum(t.getGoldNum() + e._coinsAdd),
                      cc.director.emit(s.GameEvent.TimingBox_Get_Coins);
                  }, s.ADType.TimingBoxGetReward);
              }),
              i([h(cc.Node)], t.prototype, "sprCover", void 0),
              i([h(cc.Node)], t.prototype, "sprLock", void 0),
              i([h(cc.Button)], t.prototype, "btnCollect", void 0),
              i([h(cc.Label)], t.prototype, "labText", void 0),
              i([h(cc.Label)], t.prototype, "labCoinsAdd", void 0),
              i([h(cc.SpriteFrame)], t.prototype, "spfCoins", void 0),
              i([f], t)
            );
          })(r.default);
        (n.default = g), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
      },
    ],
    Tips: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "42856WjmXtPsIiGaj4tcOxo", "Tips");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = cc._decorator,
          s = r.ccclass,
          c = r.property,
          l = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (t.labContent = null), (t.sprTipsBg = null), t;
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {}),
              (t.prototype.setContentText = function (e) {
                (this.labContent.string = e),
                  (this.sprTipsBg.height = this.labContent.node.height);
              }),
              (t.prototype.start = function () {}),
              i([c(cc.Label)], t.prototype, "labContent", void 0),
              i([c(cc.Node)], t.prototype, "sprTipsBg", void 0),
              i([s], t)
            );
          })(cc.Component);
        (n.default = l), cc._RF.pop();
      },
      {},
    ],
    Tools: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "0bee8BirLZLJ4rZ5rwU22Eq", "Tools");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/RoomInfoManager"),
          l = e("../Framework/Manager/UserInfoManager"),
          u = e("../Framework/Native/NativeBridge"),
          d = e("../Framework/Utils/Utils"),
          p = e("./AdLoading"),
          f = e("./CoinsFlyEffect"),
          h = e("./Tips"),
          g = cc._decorator,
          m = g.ccclass,
          _ = g.property,
          y = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.tipsPrefab = null),
                (t.conisFlyEffectPrefab = null),
                (t.adloadingPrefab = null),
                (t.levelUpgradExpJson = null),
                (t.signRewardJson = null),
                (t.mapInfoFourJson = null),
                (t.countryJson = null),
                (t.timingBoxRewardJson = null),
                (t.turntableRewardJson = null),
                (t.robotJson = null),
                (t.entryCoinsJson = null),
                (t.propsJson = null),
                (t.gameDifficultyJson = null),
                (t.shopJson = null),
                (t.shop2Json = null),
                (t.taskJson = null),
                (t.global = null),
                (t.online = null),
                (t.shopSkinJson = null),
                (t.item = null),
                (t.cupReward = null),
                (t.cupActivity = null),
                (t.mateList = []),
                (t.guideJson = null),
                (t.language = null),
                (t.gameInfo = null),
                (t.levelDifficulty = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  cc.game.addPersistRootNode(this.node),
                  this.schedule(function () {
                    l.default.getInstance().setOnlineTime(),
                      l.default.getInstance().setOfflineTime();
                  }, 5);
              }),
              (t.prototype.onGameEnterBackgroud = function () {
                u.default.isNative() &&
                  cc.log(
                    "---------------------- onGameEnterBackgroud ---------------"
                  );
              }),
              (t.prototype.onGameEnterForeground = function () {
                u.default.isNative() &&
                  (cc.log(
                    "---------------------- onGameEnterForeground ---------------"
                  ),
                  u.default.watchVideo(function () {},
                  s.ADType.Enter_Foreground_Insert));
              }),
              (t.prototype.onDestroy = function () {
                e.prototype.onDestroy.call(this);
              }),
              (t.prototype.registerAllEvents = function () {}),
              (t.prototype.start = function () {}),
              (t.prototype.showTips = function (e) {
                var t = cc.find("Canvas"),
                  n = t.getChildByName("TIPS_NODE");
                n && n.destroy(),
                  (n = cc.instantiate(this.tipsPrefab))
                    .getComponent(h.default)
                    .setContentText(e),
                  (n.name = "TIPS_NODE"),
                  (n.parent = t),
                  n.runAction(
                    cc.sequence(cc.delayTime(1), cc.fadeOut(1), cc.removeSelf())
                  );
              }),
              (t.prototype.popupShopView = function (e, t, n) {
                return (
                  void 0 === e && (e = s.ShopShowType.Gold),
                  void 0 === t && (t = null),
                  void 0 === n && (n = null),
                  new cc.Node()
                );
              }),
              (t.prototype.playFlyEffect = function (e, t, n, o, a) {
                void 0 === n && (n = 0);
                var i = cc.find("Canvas"),
                  r = i.getChildByName("COINS_FLY_EFFECT_NODE");
                ((r = cc.instantiate(this.conisFlyEffectPrefab)).zIndex = 11),
                  (r.parent = i),
                  (r.name = "COINS_FLY_EFFECT_NODE"),
                  r.getComponent(f.default).playFlyEffect(e, t, n, o, a);
              }),
              (t.prototype.startAdLoading = function (e) {
                var t = cc.find("Canvas"),
                  n = t.getChildByName("AD_LOADING_NODE");
                n && n.destroy(),
                  ((n = cc.instantiate(this.adloadingPrefab)).parent = t),
                  (n.name = "AD_LOADING_NODE"),
                  n.getComponent(p.default).startLoading(e);
              }),
              (t.prototype.popupADReward = function () {}),
              (t.prototype.showNoNetWorkTip = function () {
                return (
                  u.default.getNetworkStatus() != s.NetworkStatus.No ||
                  (this.showTips(d.default.replaceStr("Network Error")), !1)
                );
              }),
              (t.prototype.getSignJson = function () {
                return this.signRewardJson.json;
              }),
              (t.prototype.getMapInfoJson = function () {
                if (c.default.getInstance().getMapType() == s.MapType.Four)
                  return this.mapInfoFourJson.json;
              }),
              (t.prototype.getCountryJson = function () {
                return this.countryJson.json;
              }),
              (t.prototype.getTurntableRewwardJson = function () {
                return this.turntableRewardJson.json;
              }),
              (t.prototype.getSkinInfo = function (e) {
                e || (e = l.default.getInstance().getSkinInfo().selectSkin);
                for (var t = this.getShopJson().skin, n = 0; n < t.length; n++)
                  if (t[n].skinName == e) return t[n];
              }),
              (t.prototype.getAllSkinInfos = function () {
                return this.getShopJson().skin;
              }),
              (t.prototype.getChargeSkinInfos = function () {
                for (
                  var e = [], t = this.getAllSkinInfos(), n = 0;
                  n < t.length;
                  n++
                )
                  "true" != t[n].isFree && e.push(t[n]);
                return e;
              }),
              (t.prototype.getUnlockChargeSkinInfos = function () {
                for (
                  var e = [], t = this.getChargeSkinInfos(), n = 0;
                  n < t.length;
                  n++
                )
                  this.isSkinUnlock(t[n].skinName) && e.push(t[n]);
                return e;
              }),
              (t.prototype.getLockChargeSkinInfos = function () {
                for (
                  var e = [], t = this.getChargeSkinInfos(), n = 0;
                  n < t.length;
                  n++
                )
                  this.isSkinUnlock(t[n].skinName) || e.push(t[n]);
                return e;
              }),
              (t.prototype.isSkinUnlock = function (e) {
                if ("true" == this.getSkinInfo(e).isFree) return !0;
                var t = l.default.getInstance().getSkinInfo();
                return (
                  !!t.skinBuyStatus[e] &&
                  (!!(
                    t.skinBuyStatus[e].buyStatus == s.BuyStatus.Purchased ||
                    (t.skinBuyStatus[e] &&
                      t.skinBuyStatus[e].buyStatus == s.BuyStatus.Experience &&
                      t.skinBuyStatus[e].endTime >= d.default.getCurTimeStamp())
                  ) ||
                    void 0)
                );
              }),
              (t.prototype.isPermanentUnlock = function (e) {
                if ("true" == this.getSkinInfo(e).isFree) return !0;
                var t = l.default.getInstance().getSkinInfo();
                return !(
                  !t.skinBuyStatus[e] ||
                  t.skinBuyStatus[e].buyStatus != s.BuyStatus.Purchased
                );
              }),
              (t.prototype.getRobotJson = function () {
                return this.robotJson.json;
              }),
              (t.prototype.getLevelUpgradeExpJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.LevelExp) ||
                  this.levelUpgradExpJson.json
                );
              }),
              (t.prototype.getEntryCoinsJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.EntryCoins) ||
                  this.entryCoinsJson.json
                );
              }),
              (t.prototype.getLeveDifficulty = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(
                      s.CloudControlConfigKey.LeveDifficulty
                    ) || this.levelDifficulty.json
                );
              }),
              (t.prototype.getPropsJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.GameProps) ||
                  this.propsJson.json
                );
              }),
              (t.prototype.getTimingBoxRewardJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(
                      s.CloudControlConfigKey.TimingBoxReward
                    ) || this.timingBoxRewardJson.json
                );
              }),
              (t.prototype.getGameDifficultyJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(
                      s.CloudControlConfigKey.GameDifficulty
                    ) || this.gameDifficultyJson.json
                );
              }),
              (t.prototype.getShopJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.Shop) ||
                  this.shopJson.json
                );
              }),
              (t.prototype.getShopSkinJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.ShopSkin) ||
                  this.shopSkinJson.json
                );
              }),
              (t.prototype.getTaskJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.Task) ||
                  this.taskJson.json
                );
              }),
              (t.prototype.getGlobalJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.Global) ||
                  this.global.json
                );
              }),
              (t.prototype.getGameInfoJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.GameInfo) ||
                  this.gameInfo.json
                );
              }),
              (t.prototype.getOnlineJson = function () {
                return (
                  l.default
                    .getInstance()
                    .getCloudControlCfg(s.CloudControlConfigKey.Online) ||
                  this.online.json
                );
              }),
              (t.prototype.getShop2Json = function () {
                return this.shop2Json.json;
              }),
              (t.prototype.getGuideJson = function () {
                return this.guideJson.json;
              }),
              (t.prototype.getLanguageJson = function () {
                return this.language.json;
              }),
              (t.prototype.getItem = function () {
                return this.item.json;
              }),
              (t.prototype.getCupReward = function () {
                return this.cupReward.json;
              }),
              (t.prototype.getCupActivity = function () {
                return this.cupActivity.json;
              }),
              (t.prototype.setNodeMaterial = function (e, t) {
                var n = t ? this.mateList[0] : this.mateList[1];
                e.setMaterial(0, n);
              }),
              i([_(cc.Prefab)], t.prototype, "tipsPrefab", void 0),
              i([_(cc.Prefab)], t.prototype, "conisFlyEffectPrefab", void 0),
              i([_(cc.Prefab)], t.prototype, "adloadingPrefab", void 0),
              i([_(cc.JsonAsset)], t.prototype, "levelUpgradExpJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "signRewardJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "mapInfoFourJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "countryJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "timingBoxRewardJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "turntableRewardJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "robotJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "entryCoinsJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "propsJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "gameDifficultyJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "shopJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "shop2Json", void 0),
              i([_(cc.JsonAsset)], t.prototype, "taskJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "global", void 0),
              i([_(cc.JsonAsset)], t.prototype, "online", void 0),
              i([_(cc.JsonAsset)], t.prototype, "shopSkinJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "item", void 0),
              i([_(cc.JsonAsset)], t.prototype, "cupReward", void 0),
              i([_(cc.JsonAsset)], t.prototype, "cupActivity", void 0),
              i([_(cc.Material)], t.prototype, "mateList", void 0),
              i([_(cc.JsonAsset)], t.prototype, "guideJson", void 0),
              i([_(cc.JsonAsset)], t.prototype, "language", void 0),
              i([_(cc.JsonAsset)], t.prototype, "gameInfo", void 0),
              i([_(cc.JsonAsset)], t.prototype, "levelDifficulty", void 0),
              i([m], t)
            );
          })(r.default);
        (n.default = y), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "./AdLoading": "AdLoading",
        "./CoinsFlyEffect": "CoinsFlyEffect",
        "./Tips": "Tips",
      },
    ],
    TransitionView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "6b267qRyLlClrft+Dm/cM9v", "TransitionView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Manager/GameDataManager"),
          c = cc._decorator,
          l = c.ccclass,
          u =
            (c.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  s.default.getInstance().setIsAgain(!1),
                    cc.director.loadScene("Game_grass");
                }),
                (t.prototype.start = function () {}),
                i([l], t)
              );
            })(r.default));
        (n.default = u), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Manager/GameDataManager": "GameDataManager",
      },
    ],
    TurnHeadPhotoAnim: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "60411tRtqtJM7op2l5lxWU6", "TurnHeadPhotoAnim");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Utils/Utils"),
          l = cc._decorator,
          u = l.ccclass,
          d = l.property,
          p = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labNickName = null),
                (t.sprHeadPhotos = []),
                (t._turnOnceMoveDistance = 0),
                (t._nickName = ""),
                (t._sprShowHeadPhoto = null),
                (t._stopPostion = null),
                (t._finishCallback = null),
                (t._durationSecond = 3),
                (t._isNeedStop = !0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                (this._turnOnceMoveDistance = Math.floor(
                  Math.abs(
                    this.sprHeadPhotos[1].node.y - this.sprHeadPhotos[0].node.y
                  )
                )),
                  (this._stopPostion = this.sprHeadPhotos[0].node.position);
              }),
              (t.prototype.setInfo = function (e, t) {
                var n = this;
                this._nickName = e;
                for (var o = [], a = 1; a <= s.PLAYER_HEAD_PHOTO_COUNT; a++)
                  a != t && o.push(a);
                (o = c.default.getRandomArrayElements(
                  o,
                  this.sprHeadPhotos.length - 1
                )).push(t),
                  c.default.shuffle(o);
                var i = function (e) {
                    var a = o[e];
                    a == t && (r._sprShowHeadPhoto = r.sprHeadPhotos[e]),
                      r.loadRes(
                        s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + a,
                        cc.SpriteFrame,
                        function (t) {
                          n.sprHeadPhotos[e].spriteFrame = t;
                        }
                      );
                  },
                  r = this;
                for (a = 0; a < o.length; a++) i(a);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.startTurn = function (e) {
                var t = this;
                (this._finishCallback = e),
                  (this._isNeedStop = !1),
                  this.scheduleOnce(function () {
                    t._isNeedStop = !0;
                  }, this._durationSecond),
                  this.playTurnAnim();
              }),
              (t.prototype.playTurnAnim = function () {
                for (
                  var e = this,
                    t = function () {
                      var t = e.sprHeadPhotos[0],
                        n = e.sprHeadPhotos[e.sprHeadPhotos.length - 1];
                      (t.node.y = n.node.y + e._turnOnceMoveDistance),
                        e.sprHeadPhotos.splice(0, 1),
                        e.sprHeadPhotos.push(t),
                        e.playTurnAnim();
                    },
                    n = 0;
                  n < this.sprHeadPhotos.length;
                  n++
                )
                  n == this.sprHeadPhotos.length - 1
                    ? this.sprHeadPhotos[n].node.runAction(
                        cc.sequence(
                          cc.moveBy(0.1, cc.v2(0, -this._turnOnceMoveDistance)),
                          cc.callFunc(function () {
                            e._isNeedStop &&
                            Math.floor(
                              Math.abs(
                                e._sprShowHeadPhoto.node.y - e._stopPostion.y
                              )
                            ) < 21
                              ? ((e.labNickName.string = e._nickName),
                                e._finishCallback())
                              : t();
                          })
                        )
                      )
                    : this.sprHeadPhotos[n].node.runAction(
                        cc.moveBy(0.1, cc.v2(0, -this._turnOnceMoveDistance))
                      );
              }),
              i([d(cc.Label)], t.prototype, "labNickName", void 0),
              i([d(cc.Sprite)], t.prototype, "sprHeadPhotos", void 0),
              i([u], t)
            );
          })(r.default);
        (n.default = p), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    TurntableView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "22270j1rc9MbZbwHnweXjuk", "TurntableView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameConst"),
          c = e("../../Framework/Enum/GameEnum"),
          l = e("../../Framework/Manager/AudioManager"),
          u = e("../../Framework/Manager/BuriedPointManager"),
          d = e("../../Framework/Manager/GameDataManager"),
          p = e("../../Framework/Manager/GlobalTimerManager"),
          f = e("../../Framework/Manager/UserInfoManager"),
          h = e("../../Framework/Native/NativeBridge"),
          g = e("../../Framework/Utils/Utils"),
          m = e("./GetRewardView"),
          _ = e("../../Framework/Manager/TaskManager"),
          y = cc._decorator,
          v = y.ccclass,
          I = y.property,
          C = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.turntableBg = null),
                (t.btnSpin = null),
                (t.btnSpinAgain = null),
                (t.nodeSheild = null),
                (t.nodeArrow = null),
                (t.arrowAnim = null),
                (t.img_spin = null),
                (t.material_List = []),
                (t.node_time = null),
                (t.label_luckyTime = null),
                (t.btn_lucky = null),
                (t.label_lucky = null),
                (t.node_guide2 = null),
                (t.node_guide3 = null),
                (t.node_dianji2 = null),
                (t.node_dianji3 = null),
                (t._rewards = null),
                (t._durationSecond = 5),
                (t._rotateCircleCount = 10),
                (t._rewardCoins = 0),
                (t._goldSelect = [500, 1e3, 1500, 2e3]),
                (t.selectGold = 500),
                (t.goldIndex = 0),
                (t.isSpin = !1),
                (t.rewardscoefficient = [
                  0, 0.2, 0.5, 0.8, 1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 25,
                ]),
                (t.rewardsProbability = [
                  20, 180, 350, 530, 750, 870, 910, 940, 960, 975, 983, 989,
                  994, 997, 999, 1e3,
                ]),
                (t.endTime = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                f.default.getInstance().isShowAppluck(!0),
                  f.default.getInstance().getMyselfUserInfo(),
                  g.default.localStr(this.node),
                  this.registerAllEvents(),
                  this.initTurntable(),
                  this.initCD();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Turntable_Show_Get_Reward,
                  this.showGetReward,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Turntable_Spin_Again,
                    this.onSpinAgain,
                    this
                  );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.initTurntable = function () {
                var e = d.default
                  .getInstance()
                  .getTools()
                  .getTurntableRewwardJson().rewards;
                this._rewards = e;
                for (var t = 0; t < e.length; t++) {
                  var n = this.turntableBg.getChildByName("truntableItem" + t);
                  n &&
                    (n
                      .getChildByName("labelReward")
                      .getComponent(cc.Label).string =
                      "" + e[t].coins * this.selectGold);
                }
                this.nodeArrow.active = !1;
              }),
              (t.prototype.updateSelectGold = function () {}),
              (t.prototype.updateBtnStarts = function () {}),
              (t.prototype.onBtnAddClick = function () {
                this.isSpin ||
                  (this.goldIndex + 1 <= this._goldSelect.length - 1 &&
                    (this.goldIndex++,
                    (this.selectGold = this._goldSelect[this.goldIndex])),
                  this.updateSelectGold(),
                  this.updateBtnStarts(),
                  this.initTurntable());
              }),
              (t.prototype.onBtnReduceClick = function () {
                this.isSpin ||
                  (this.goldIndex - 1 >= 0 &&
                    (this.goldIndex--,
                    (this.selectGold = this._goldSelect[this.goldIndex])),
                  this.updateSelectGold(),
                  this.updateBtnStarts(),
                  this.initTurntable());
              }),
              (t.prototype.rotateTurntable = function () {
                (this.turntableBg.rotation = 0),
                  this.turntableBg.runAction(
                    cc.repeatForever(cc.rotateBy(10, 360))
                  );
              }),
              (t.prototype.showArrowAnim = function (e) {
                (this.nodeArrow.active = e),
                  e ? this.arrowAnim.play("jiantou") : this.arrowAnim.stop();
              }),
              (t.prototype.initCD = function () {
                var e = f.default.getInstance().getNewTurntableInfo();
                (this.img_spin.spriteFrame = e.isCanFree
                  ? this.material_List[0]
                  : this.material_List[1]),
                  (this.btnSpin.interactable = e.isCanFree),
                  (e.showLucky || 0 != e.spinTime) &&
                    ((this.btnSpinAgain.active = !0),
                    (this.endTime =
                      (e.spinTime + 18e4 - g.default.getCurTimeStamp()) / 1e3),
                    (this.node_time.active = this.endTime > 0),
                    this.endTime > 0 &&
                      (this.updateTime(),
                      (this.btn_lucky.interactable = !1),
                      (this.label_lucky.color = s.GREY),
                      this.schedule(this.updateTime, 1)));
              }),
              (t.prototype.updateTime = function () {
                if (this.endTime > 0)
                  this.endTime--,
                    (this.label_luckyTime.string = g.default.formatTime(
                      this.endTime
                    ));
                else {
                  (this.endTime = 0),
                    (this.btn_lucky.interactable = !0),
                    (this.label_lucky.color = s.BLUE),
                    (this.node_time.active = !1);
                  var e = f.default.getInstance().getNewTurntableInfo();
                  f.default
                    .getInstance()
                    .setNewTurntableInfo(
                      !1,
                      !0,
                      e.spinTime,
                      g.default.getDateString()
                    ),
                    this.unschedule(this.updateTime);
                }
              }),
              (t.prototype.startSpin = function () {
                var e = this;
                this.showArrowAnim(!1),
                  this.turntableBg.stopAllActions(),
                  (this.turntableBg.rotation = 0),
                  (this.btnSpin.interactable = !1);
                for (
                  var t = g.default.getRandomNum(1, 1e3), n = 0, o = 0;
                  o < this.rewardsProbability.length;
                  o++
                )
                  if (t <= this.rewardsProbability[o]) {
                    n = this.rewardscoefficient[o];
                    break;
                  }
                var a = this.getGoldIndex(n);
                this._rewardCoins = this._rewards[a].coins;
                var i =
                  360 * this._rotateCircleCount +
                  a * (360 / this._rewards.length);
                this.turntableBg.runAction(
                  cc.sequence(
                    cc
                      .rotateTo(this._durationSecond, i)
                      .easing(cc.easeCubicActionInOut()),
                    cc.callFunc(function () {
                      (e.btnSpin.interactable = !1),
                        d.default.getInstance().setIsAd(!1),
                        _.default
                          .getInstance()
                          .setTaskProgress(c.TaskType.Task_turntable),
                        e.showRewardDouble();
                    })
                  )
                );
              }),
              (t.prototype.getGoldIndex = function (e) {
                for (var t = 0, n = 0; n < this._rewards.length; n++)
                  if (this._rewards[n].coins == e) {
                    t = n;
                    break;
                  }
                return t;
              }),
              (t.prototype.showRewardDouble = function () {
                var e = this,
                  t = f.default.getInstance().getMyselfUserInfo();
                0 != this._rewardCoins &&
                  d.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(
                      c.FlyEffectType.Coins,
                      cc.v3(0, 0, 0),
                      this._rewardCoins * this.selectGold,
                      function () {
                        t.setGoldNum(
                          t.getGoldNum() + e._rewardCoins * e.selectGold
                        );
                      }
                    ),
                  (this.isSpin = !1),
                  this.initCD();
              }),
              (t.prototype.onBtnLuckyClick = function () {
                var e = this;
                f.default.getInstance().getNewTurntableInfo().showLucky &&
                  h.default.watchVideo(function () {
                    (e.node_guide3.active = !1),
                      (e.node_dianji3.active = !1),
                      e.onClickSpin(),
                      f.default
                        .getInstance()
                        .setNewTurntableInfo(
                          !1,
                          !1,
                          g.default.getCurTimeStamp(),
                          g.default.getDateString()
                        ),
                      e.initCD();
                  }, c.ADType.TurntableSpinAgain);
              }),
              (t.prototype.showGetReward = function (e) {
                var t = this;
                this.loadRes(
                  s.HALL_PREFAB_PATH + "turntable/GetRewardView",
                  cc.Prefab,
                  function (n) {
                    var o = cc.instantiate(n);
                    (o.parent = t.node), o.getComponent(m.default).setInfo(e);
                  }
                );
              }),
              (t.prototype.onClickSpin = function () {
                var e = f.default.getInstance().getNewTurntableInfo();
                (1 != e.isCanFree && 1 != e.showLucky) ||
                  ((this.isSpin = !0),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.TurntableStart,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.TurntableStart,
                    }),
                  f.default
                    .getInstance()
                    .setNewTurntableInfo(!1, !0, 0, g.default.getDateString()),
                  this.startSpin(),
                  (this.node_guide2.active = !1),
                  (this.node_dianji2.active = !1),
                  h.default.preloadReward(c.ADType.TurntableDoubleUp));
              }),
              (t.prototype.onClickSpinAgain = function () {
                var e = this;
                l.default
                  .getInstance()
                  .playEffectWithPath(c.AudioType.Button_Click),
                  d.default.getInstance().getTools().showNoNetWorkTip() &&
                    (h.default.watchVideo(function () {
                      p.default.getInstance().closeTurntableTimer();
                      var t = f.default.getInstance().getTurntableInfo();
                      f.default
                        .getInstance()
                        .setTurntableInfo(
                          0,
                          t.leftSpinCount - 1,
                          t.adbonus - 1,
                          !0
                        ),
                        e.onSpinAgain(),
                        d.default.getInstance().setIsAd(!0);
                    }, c.ADType.TurntableSpinAgain),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.CommonClick,
                        clickType: c.ButtonClickType.TurntableSpinAgain,
                      }),
                    u.default
                      .getInstance()
                      .sendBuriedPointInfo({
                        event: c.BuriedPointKey.CommonClick,
                        actionName: c.BuriedPointSecondKey.clickType,
                        value: c.ButtonClickType.TurntableSpinAgain,
                      }));
              }),
              (t.prototype.onSpinAgain = function () {
                (this.nodeSheild.active = !1),
                  (this.btnSpinAgain.active = !1),
                  this.showArrowAnim(!1);
              }),
              (t.prototype.onClickClose = function () {
                h.default.closeBanner(),
                  cc.director.emit(c.GameEvent.Close_Parent_Ui),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedOneKey.enterGameHall,
                      actionName: c.BuriedTwoKey.fromLuckWheel,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      clickType: c.ButtonClickType.TurntableQuit,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.CommonClick,
                      actionName: c.BuriedPointSecondKey.clickType,
                      value: c.ButtonClickType.TurntableQuit,
                    }),
                  this.onClose();
              }),
              (t.prototype.onBtnCloseGuideClick = function () {
                (this.node_dianji3.active = !1), (this.node_guide3.active = !1);
              }),
              i([I(cc.Node)], t.prototype, "turntableBg", void 0),
              i([I(cc.Button)], t.prototype, "btnSpin", void 0),
              i([I(cc.Node)], t.prototype, "btnSpinAgain", void 0),
              i([I(cc.Node)], t.prototype, "nodeSheild", void 0),
              i([I(cc.Node)], t.prototype, "nodeArrow", void 0),
              i([I(cc.Animation)], t.prototype, "arrowAnim", void 0),
              i([I(cc.Sprite)], t.prototype, "img_spin", void 0),
              i([I(cc.SpriteFrame)], t.prototype, "material_List", void 0),
              i([I(cc.Node)], t.prototype, "node_time", void 0),
              i([I(cc.Label)], t.prototype, "label_luckyTime", void 0),
              i([I(cc.Button)], t.prototype, "btn_lucky", void 0),
              i([I(cc.LabelOutline)], t.prototype, "label_lucky", void 0),
              i([I(cc.Node)], t.prototype, "node_guide2", void 0),
              i([I(cc.Node)], t.prototype, "node_guide3", void 0),
              i([I(cc.Node)], t.prototype, "node_dianji2", void 0),
              i([I(cc.Node)], t.prototype, "node_dianji3", void 0),
              i([v], t)
            );
          })(r.default);
        (n.default = C), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameConst": "GameConst",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/AudioManager": "AudioManager",
        "../../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/GlobalTimerManager": "GlobalTimerManager",
        "../../Framework/Manager/TaskManager": "TaskManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../../Framework/Native/NativeBridge": "NativeBridge",
        "../../Framework/Utils/Utils": "Utils",
        "./GetRewardView": "GetRewardView",
      },
    ],
    UndoDice: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "76ac0lsJ3dACL2DPFjKDALj", "UndoDice");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/GameDataManager"),
          l = e("../Framework/Native/NativeBridge"),
          u = e("../Framework/Utils/Utils"),
          d = cc._decorator,
          p = d.ccclass,
          f =
            (d.property,
            (function (e) {
              function t() {
                var t = (null !== e && e.apply(this, arguments)) || this;
                return (t._diceNum = 0), t;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  u.default.localStr(this.node),
                    l.default.preloadReward(s.ADType.ShowUndoDice);
                }),
                (t.prototype.setDiceNum = function (e) {
                  (this._diceNum = e), c.default.getInstance().setDicePoints(e);
                }),
                (t.prototype.onBtnCloseClick = function () {
                  cc.director.emit(s.GameEvent.Close_Undo_Dice), this.onClose();
                }),
                (t.prototype.onBtnLoadClick = function () {
                  var e = this;
                  l.default.getRewardLoadType()
                    ? (cc.director.pause(),
                      l.default.watchVideo(function () {
                        cc.director.resume();
                        var t = u.default.getRandomNum(1, 6);
                        c.default.getInstance().setDicePoints(t),
                          cc.director.emit(s.GameEvent.Close_Undo_Dice),
                          e.onClose();
                      }, s.ADType.ShowUndoDice))
                    : c.default
                        .getInstance()
                        .getTools()
                        .showTips(u.default.replaceStr("Network Error"));
                }),
                i([p], t)
              );
            })(r.default));
        (n.default = f), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    UndoHelp: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "23debXdkUpFjogVfIT56Auw", "UndoHelp");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Utils/Utils"),
          c = cc._decorator,
          l = c.ccclass,
          u = c.property,
          d = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.btn_left = null),
                (t.btn_right = null),
                (t.page_view = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                (this.btn_left.active = !1),
                  (this.btn_right.active = !0),
                  s.default.localStr(this.node),
                  this.page_view.scrollToPage(0, 0.3);
              }),
              (t.prototype.onBtnLeftClick = function () {
                (this.btn_left.active = !1),
                  (this.btn_right.active = !0),
                  this.page_view.scrollToPage(0, 0.3);
              }),
              (t.prototype.onBtnRightClick = function () {
                (this.btn_left.active = !0),
                  (this.btn_right.active = !1),
                  this.page_view.scrollToPage(1, 0.3);
              }),
              i([u(cc.Node)], t.prototype, "btn_left", void 0),
              i([u(cc.Node)], t.prototype, "btn_right", void 0),
              i([u(cc.PageView)], t.prototype, "page_view", void 0),
              i([l], t)
            );
          })(r.default);
        (n.default = d), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    UpgradeRewardView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "bb706Iu84pObr5w2fFw6R3c", "UpgradeRewardView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/AudioManager"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Native/NativeBridge"),
          p = e("../Framework/Utils/Utils"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprGold = null),
                (t.sprDiamond = null),
                (t.labGold = null),
                (t.labDiamond = null),
                (t.labLevel = null),
                (t._getCoins = 0),
                (t._getDiamonds = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                p.default.localStr(this.node);
                var e = u.default.getInstance().getMyselfUserInfo().getLevel(),
                  t = e - 1,
                  n = l.default
                    .getInstance()
                    .getTools()
                    .getLevelUpgradeExpJson().infos[t - 1];
                (this._getCoins = n.levelUpReward.coins),
                  (this._getDiamonds = n.levelUpReward.diamonds),
                  console.log(
                    "upgrade: " +
                      this._getCoins +
                      "this._getDiamonds : " +
                      this._getDiamonds +
                      "curLevel: " +
                      e
                  ),
                  (this.labGold.string = this._getCoins.toString()),
                  (this.labDiamond.string = this._getDiamonds.toString()),
                  (this.labLevel.string = e.toString()),
                  d.default.preloadReward(s.ADType.UpgradeReward);
              }),
              (t.prototype.start = function () {}),
              (t.prototype.onClickGot = function () {
                var e = this;
                c.default
                  .getInstance()
                  .playEffectWithPath(s.AudioType.Button_Click),
                  d.default.watchVideo(function () {
                    var t = l.default.getInstance().getHallGoldPos(),
                      n = p.default.getWorldPosition(e.sprGold);
                    l.default
                      .getInstance()
                      .getTools()
                      .playFlyEffect(
                        s.FlyEffectType.Coins,
                        t,
                        e._getCoins,
                        function () {
                          var t = u.default.getInstance().getMyselfUserInfo();
                          t.setGoldNum(t.getGoldNum() + e._getCoins);
                        },
                        n
                      ),
                      e.onClose();
                  }, s.ADType.UpgradeReward);
              }),
              i([g(cc.Node)], t.prototype, "sprGold", void 0),
              i([g(cc.Node)], t.prototype, "sprDiamond", void 0),
              i([g(cc.Label)], t.prototype, "labGold", void 0),
              i([g(cc.Label)], t.prototype, "labDiamond", void 0),
              i([g(cc.Label)], t.prototype, "labLevel", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    Upgrade: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "3f131kUEPZGTrL0tcV3jnT8", "Upgrade");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = cc._decorator,
          c = s.ccclass,
          l = s.property,
          u = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.labLv = null),
                (t.animation = null),
                (t._nextLv = 0),
                (t._finishCallback = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.setInfo = function (e, t, n) {
                var o,
                  a = this;
                (this.labLv.string = e.toString()),
                  (this._nextLv = t),
                  (this._finishCallback = n),
                  this.animation.play("shengji"),
                  (o = function () {
                    a.animation.off("finished", o),
                      a.node.runAction(
                        cc.sequence(
                          cc.delayTime(0.5),
                          cc.callFunc(function () {
                            a._finishCallback(), a.onClose();
                          })
                        )
                      );
                  }),
                  this.animation.on("finished", o);
              }),
              (t.prototype.onChangeLevel = function () {
                console.log("onChangeLevel"),
                  (this.labLv.string = this._nextLv.toString());
              }),
              (t.prototype.start = function () {}),
              i([l(cc.Label)], t.prototype, "labLv", void 0),
              i([l(cc.Animation)], t.prototype, "animation", void 0),
              i([c], t)
            );
          })(r.default);
        (n.default = u), cc._RF.pop();
      },
      { "../Framework/Base/BaseComponent": "BaseComponent" },
    ],
    UsePropsView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "5847em3XztGGpGy7Usq7Jld", "UsePropsView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/AudioManager"),
          u = e("../Framework/Manager/BuriedPointManager"),
          d = e("../Framework/Manager/ChessManager"),
          p = e("../Framework/Manager/GameDataManager"),
          f = e("../Framework/Manager/LuckManager"),
          h = e("../Framework/Manager/RoomInfoManager"),
          g = e("../Framework/Manager/UserInfoManager"),
          m = e("../Framework/Native/NativeBridge"),
          _ = e("../Framework/Utils/Utils"),
          y = cc._decorator,
          v = y.ccclass,
          I = y.property,
          C = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.btnAgainRoll = null),
                (t.sprAgainRoll = null),
                (t.labAgainCost = null),
                (t.label_undo = null),
                (t.btnBomb = null),
                (t.node_bomb = null),
                (t.node_again = null),
                (t.spr_item = null),
                (t.sprItemList = []),
                (t.labBombCost = null),
                (t._perMinusValueAgain = 0),
                (t._AgainRollCount = 0),
                (t._propDoubleDiceUseCount = 0),
                (t._propProtectiveUseCount = 0),
                (t._propBombUseCount = 0),
                (t._propAgainUseCount = 0),
                (t._bombOriginalPos = null),
                (t._protectiveOriginalPos = null),
                (t._playerInfo = null),
                (t._dragPropTipsView = null),
                (t._isAgainRollEnabled = !1),
                (t._PLATER_AGAIN_ROLL_COUNT = 0),
                (t._PLAYER_AGAIN_ROLL_CD_TIME = 0),
                (t._playerIndex = 0),
                (t._bombMax = 3),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  _.default.localStr(this.node),
                  this.setPropsCanUse(!1);
                var e = p.default.getInstance().getTools().getGlobalJson();
                (this._PLATER_AGAIN_ROLL_COUNT = e.info[0].round_max),
                  (this._PLAYER_AGAIN_ROLL_CD_TIME =
                    s.PLAYER_AGAIN_ROLL_CD_TIME),
                  h.default.getInstance().getGameMode() == c.GameMode.Local &&
                    (this._PLAYER_AGAIN_ROLL_CD_TIME = 0.01),
                  this.updateBomb();
                var t = h.default.getInstance().getGameMode();
                (this.node_bomb.active =
                  h.default.getInstance().getGameMode() == c.GameMode.BombItem),
                  (this.node_again.active = !(
                    h.default.getInstance().getGameMode() == c.GameMode.BombItem
                  )),
                  t == c.GameMode.BombItem || t == c.GameMode.Roadblock
                    ? ((this.node_bomb.active = !0),
                      (this.node_again.active = !1),
                      (this.spr_item.spriteFrame =
                        t == c.GameMode.BombItem
                          ? this.sprItemList[0]
                          : this.sprItemList[1]))
                    : ((this.node_bomb.active = !1),
                      (this.node_again.active = !0));
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Use_Undo,
                  this.updateUndoCount,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Turn_Player_Operation,
                    this.onOperation,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.AD_Cache_Fail,
                    this.ADCache,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.UpdateBombCount,
                    this.updateBomb,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.ShowBomb,
                    this.updateBomb,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.ShowBombHelpTip,
                    this.hideBombItem,
                    this
                  );
              }),
              (t.prototype.onOperation = function (e) {
                (this._playerIndex = e),
                  this._playerIndex !=
                  g.default.getInstance().getMyselfUserInfo().getPlayerIndex()
                    ? (this.sprAgainRoll.node.active = !0)
                    : (this.sprAgainRoll.node.active = !1);
              }),
              (t.prototype.setInfo = function (e) {
                (this._playerInfo = e), this.updateUndoCount();
              }),
              (t.prototype.hideBombItem = function () {
                this.btnBomb.interactable = !1;
              }),
              (t.prototype.updateBomb = function () {
                var e = g.default.getInstance().getMyselfUserInfo(),
                  t = p.default.getInstance().getBomb(e.getPlayerIndex());
                (this.labBombCost.string =
                  this._bombMax - t + "/" + this._bombMax),
                  this._bombMax - t <= 0 && (this.btnBomb.interactable = !1);
              }),
              (t.prototype.setDoubleDiceActive = function () {}),
              (t.prototype.setPropsCanUse = function (e) {
                if (e) {
                  this.setDoubleDiceActive(!0);
                  var t = g.default.getInstance().getMyselfUserInfo(),
                    n = p.default.getInstance().getBomb(t.getPlayerIndex());
                  this.btnBomb.interactable = this._bombMax - n > 0;
                } else
                  this.setDoubleDiceActive(!1),
                    (this.btnBomb.interactable = !1);
              }),
              (t.prototype.updateUndoCount = function () {
                (this.label_undo.string =
                  p.default.getInstance().getGameUndoCount() + "/5"),
                  (this.labAgainCost.string = this.getUsePropCost(
                    c.PropType.AgainRoll
                  ));
              }),
              (t.prototype.onClickDoubleDice = function () {
                if (
                  this.checkCostDiamondEnough(c.PropType.DoubleDice) &&
                  !this.checkUsePropCountLimit(c.PropType.DoubleDice)
                ) {
                  this._playerInfo.setDiceButtonActive(!1),
                    cc.director.emit(c.GameEvent.Hide_Dice_TestUI);
                  var e =
                      f.default.getInstance().getDefaultDicePoints() +
                      f.default.getInstance().getDefaultDicePoints(),
                    t = this._playerInfo.getDicePoints(e);
                  this._playerInfo.setCurRollDicePoints(t),
                    this._playerInfo.stopTurnPlayerAnim(),
                    l.default.getInstance().stopAllEffect(),
                    l.default
                      .getInstance()
                      .playEffectWithPath(c.AudioType.Roll_Dice),
                    this.usePropSuccess(c.PropType.DoubleDice);
                }
              }),
              (t.prototype.removeDragPropTipsView = function () {
                this._dragPropTipsView &&
                  (this._dragPropTipsView.destroy(),
                  (this._dragPropTipsView = null));
              }),
              (t.prototype.showDragPropTipsView = function (e) {
                this.removeDragPropTipsView(),
                  p.default.getInstance().isShowPropTips(e);
              }),
              (t.prototype.showBomb = function () {
                this.showDragPropTipsView(c.PropType.Bomb);
              }),
              (t.prototype.bombTouchMove = function (e) {
                this.removeDragPropTipsView(), e.getLocation();
              }),
              (t.prototype.bombTouchEnd = function (e) {
                var t = e.getLocation();
                d.default.getInstance().checkBombUseSuccess(t)
                  ? (this.hideBomb(), this.usePropSuccess(c.PropType.Bomb))
                  : p.default
                      .getInstance()
                      .getTools()
                      .showTips("Please drag the pawn to the blank square");
              }),
              (t.prototype.hideBomb = function () {}),
              (t.prototype.showProtective = function () {
                this.showDragPropTipsView(c.PropType.Protective);
              }),
              (t.prototype.protectiveTouchMove = function (e) {
                this.removeDragPropTipsView(), e.getLocation();
              }),
              (t.prototype.protectiveTouchEnd = function (e) {
                var t = e.getLocation();
                d.default.getInstance().checkProtectiveUseSuccess(t) &&
                  (this.hideProtective(),
                  this.usePropSuccess(c.PropType.Protective));
              }),
              (t.prototype.hideProtective = function () {}),
              (t.prototype.onClickBomb = function () {
                this.checkCostDiamondEnough(c.PropType.Bomb) &&
                  !this.checkUsePropCountLimit(c.PropType.Bomb) &&
                  this.showBomb();
              }),
              (t.prototype.onClickProtective = function () {
                this.checkCostDiamondEnough(c.PropType.Protective) &&
                  !this.checkUsePropCountLimit(c.PropType.Protective) &&
                  this.showProtective();
              }),
              (t.prototype.getUsePropCost = function (e) {
                var t = this.getPropInfo(e),
                  n = null;
                if (e == c.PropType.AgainRoll) {
                  var o = p.default.getInstance().getGameUndoCount();
                  n = p.default.getInstance().getTools().getGlobalJson().info[0]
                    .undo_gold[5 - o];
                } else
                  e == c.PropType.Bomb
                    ? (n =
                        0 == this._propBombUseCount
                          ? t.firstCost
                          : t.firstCost +
                            this._propAgainUseCount * t.perAddCost)
                    : e == c.PropType.DoubleDice
                    ? (n =
                        0 == this._propDoubleDiceUseCount
                          ? t.firstCost
                          : t.firstCost +
                            this._propAgainUseCount * t.perAddCost)
                    : e == c.PropType.Protective &&
                      (n =
                        0 == this._propProtectiveUseCount
                          ? t.firstCost
                          : t.firstCost +
                            this._propAgainUseCount * t.perAddCost);
                return n;
              }),
              (t.prototype.setUsePropCost = function (e) {
                var t = this.getUsePropCost(e);
                e == c.PropType.AgainRoll
                  ? (this.labAgainCost.string = "-" + t)
                  : e == c.PropType.Bomb ||
                    e == c.PropType.DoubleDice ||
                    c.PropType.Protective;
              }),
              (t.prototype.usePropSuccess = function (e) {
                var t = g.default.getInstance().getMyselfUserInfo(),
                  n = this.getUsePropCost(e),
                  o = t.getDiamondNum() - n;
                t.setDiamondNum(o),
                  e == c.PropType.AgainRoll
                    ? (this._propAgainUseCount += 1)
                    : e == c.PropType.Bomb
                    ? (this._propBombUseCount += 1)
                    : e == c.PropType.DoubleDice
                    ? (this._propDoubleDiceUseCount += 1)
                    : e == c.PropType.Protective &&
                      (this._propProtectiveUseCount += 1),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.UseProp,
                      propType: e,
                    }),
                  u.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: c.BuriedPointKey.UseProp,
                      actionName: c.BuriedPointSecondKey.propType,
                      value: e,
                    });
              }),
              (t.prototype.checkCostDiamondEnough = function (e) {
                var t = g.default.getInstance().getMyselfUserInfo();
                return this.getUsePropCost(e), t.getDiamondNum(), !0;
              }),
              (t.prototype.getPropInfo = function (e) {
                for (
                  var t = p.default.getInstance().getTools().getPropsJson(),
                    n = 0;
                  n < t.infos.length;
                  n++
                )
                  if (t.infos[n].propType == e) return t.infos[n];
              }),
              (t.prototype.checkUsePropCountLimit = function (e) {
                var t = this.getPropInfo(e).useCountLimit;
                return e == c.PropType.DoubleDice &&
                  this._propDoubleDiceUseCount == t
                  ? (p.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        "The number of times this prop can be used in this game has reached the upper limit"
                      ),
                    !0)
                  : e == c.PropType.Bomb && this._propBombUseCount == t
                  ? (p.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        "The number of times this prop can be used in this game has reached the upper limit"
                      ),
                    !0)
                  : e == c.PropType.Protective &&
                    this._propProtectiveUseCount == t
                  ? (p.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        "The number of times this prop can be used in this game has reached the upper limit"
                      ),
                    !0)
                  : e == c.PropType.AgainRoll && this._propAgainUseCount > t;
              }),
              (t.prototype.onClickAgain = function () {
                var e = this;
                m.default.preloadReward(c.ADType.ShowUndoAgain),
                  l.default
                    .getInstance()
                    .playEffectWithPath(c.AudioType.Button_Click),
                  this.checkCostDiamondEnough(c.PropType.AgainRoll) &&
                    (this.checkUsePropCountLimit(c.PropType.AgainRoll) ||
                      (this._playerIndex ==
                        g.default
                          .getInstance()
                          .getMyselfUserInfo()
                          .getPlayerIndex() &&
                        1 != this.sprAgainRoll.node.active &&
                        (m.default.getRewardLoadType()
                          ? (cc.director.pause(),
                            m.default.watchVideo(function () {
                              cc.director.resume(),
                                p.default.getInstance().setUndoCount(),
                                e.closeAgainRollCD(),
                                (e.sprAgainRoll.node.active = !0),
                                e._AgainRollCount++,
                                cc.director.emit(c.GameEvent.Show_Undo_Node);
                            }, c.ADType.ShowUndoAgain))
                          : p.default
                              .getInstance()
                              .getTools()
                              .showTips(
                                _.default.replaceStr("Network Error")
                              ))));
              }),
              (t.prototype.ADCache = function () {
                cc.director.resume();
              }),
              (t.prototype.startAgainRollCD = function () {
                if (
                  !this.checkUsePropCountLimit(c.PropType.AgainRoll) &&
                  !h.default.getInstance().getIsOverTime()
                ) {
                  var e = this._PLAYER_AGAIN_ROLL_CD_TIME / 0.05;
                  (this._perMinusValueAgain = 1 / e),
                    (this._isAgainRollEnabled =
                      this._AgainRollCount <= this._PLATER_AGAIN_ROLL_COUNT),
                    this.schedule(this.againRollCDTimer, 0.05);
                }
              }),
              (t.prototype.againRollCDTimer = function () {
                this.sprAgainRoll.fillRange - this._perMinusValueAgain <= 0 &&
                  (this._playerInfo.againRollCDOver(), this.closeAgainRollCD());
              }),
              (t.prototype.closeAgainRollCD = function () {
                this.unschedule(this.againRollCDTimer),
                  (this._isAgainRollEnabled = !1),
                  (this._perMinusValueAgain = 0);
              }),
              (t.prototype.reset = function () {
                (this._AgainRollCount = 0),
                  this.removeDragPropTipsView(),
                  this.hideBomb(),
                  this.hideProtective(),
                  this.setPropsCanUse(!1),
                  this.closeAgainRollCD();
              }),
              (t.prototype.isAgainRoll = function () {
                return (
                  p.default.getInstance().getGameUndoCount(),
                  p.default.getInstance().getTools().getGlobalJson().info[0]
                    .undo_gold,
                  g.default.getInstance().getMyselfUserInfo(),
                  !0
                );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.getUsePropsInfo = function () {
                return [
                  {
                    propType: c.PropType.AgainRoll,
                    useCount: this._propAgainUseCount,
                  },
                  {
                    propType: c.PropType.Bomb,
                    useCount: this._propBombUseCount,
                  },
                  {
                    propType: c.PropType.DoubleDice,
                    useCount: this._propDoubleDiceUseCount,
                  },
                  {
                    propType: c.PropType.Protective,
                    useCount: this._propProtectiveUseCount,
                  },
                ];
              }),
              (t.prototype.onBtnShowUndoHelpClick = function () {
                cc.director.emit(c.GameEvent.Show_Undo_Help);
              }),
              (t.prototype.onBtnBombClick = function () {
                var e = g.default.getInstance().getMyselfUserInfo();
                p.default.getInstance().getBomb(e.getPlayerIndex()) <
                  this._bombMax &&
                  cc.director.emit(c.GameEvent.ShowBombHelpTip, !0);
              }),
              i([I(cc.Button)], t.prototype, "btnAgainRoll", void 0),
              i([I(cc.Sprite)], t.prototype, "sprAgainRoll", void 0),
              i([I(cc.Label)], t.prototype, "labAgainCost", void 0),
              i([I(cc.Label)], t.prototype, "label_undo", void 0),
              i([I(cc.Button)], t.prototype, "btnBomb", void 0),
              i([I(cc.Node)], t.prototype, "node_bomb", void 0),
              i([I(cc.Node)], t.prototype, "node_again", void 0),
              i([I(cc.Sprite)], t.prototype, "spr_item", void 0),
              i([I(cc.SpriteFrame)], t.prototype, "sprItemList", void 0),
              i([I(cc.Label)], t.prototype, "labBombCost", void 0),
              i([v], t)
            );
          })(r.default);
        (n.default = C), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/AudioManager": "AudioManager",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/ChessManager": "ChessManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/LuckManager": "LuckManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    UserInfoManager: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "36fc8CYrtpD5o9rNCzFIMjq", "UserInfoManager"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.UserInfo = void 0);
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("../Native/NativeBridge"),
          r = e("../Utils/Utils"),
          s = e("./BuriedPointManager"),
          c = e("./GameDataManager"),
          l = e("./GlobalTimerManager"),
          u = e("./RoomInfoManager"),
          d = e("./ShopDataManager"),
          p = (function () {
            function e(e) {
              (this._userInfoStruct = null),
                (this._isRobot = !1),
                (this._luckValue = 0),
                (this._actualLuckValue = 0),
                (this._totoalChangeLuckValues = {}),
                (this._userInfoStruct = e);
            }
            return (
              (e.prototype.getUserId = function () {
                return this._userInfoStruct.userId;
              }),
              (e.prototype.setUserId = function (e) {
                this._userInfoStruct.userId = e;
              }),
              (e.prototype.isMyself = function () {
                return (
                  this._userInfoStruct.userId ==
                  f.getInstance().getMyselfUserInfo().getUserId()
                );
              }),
              (e.prototype.getNickName = function () {
                return this._userInfoStruct.nickName;
              }),
              (e.prototype.setNickName = function (e) {
                (this._userInfoStruct.nickName = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_Nick_Name, e));
              }),
              (e.prototype.getCountryCode = function () {
                return this._userInfoStruct.countryCode;
              }),
              (e.prototype.setCountryCode = function (e) {
                (this._userInfoStruct.countryCode = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_Country_Code, e));
              }),
              (e.prototype.getCountryName = function () {
                var e = c.default.getInstance().getTools().getCountryJson();
                if ("" == this._userInfoStruct.countryCode) return "";
                var t = parseInt(this._userInfoStruct.countryCode),
                  n = e.countries[t];
                return n ? n.countryName : "";
              }),
              (e.prototype.getGoldNum = function () {
                return this._userInfoStruct.goldNum;
              }),
              (e.prototype.setGoldNum = function (e) {
                (this._userInfoStruct.goldNum = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_Gold_Num, e));
              }),
              (e.prototype.getDiamondNum = function () {
                return this._userInfoStruct.diamondNum;
              }),
              (e.prototype.setDiamondNum = function (e) {
                (this._userInfoStruct.diamondNum = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_Diamond_Num, e));
              }),
              (e.prototype.getLevel = function () {
                return this._userInfoStruct.level;
              }),
              (e.prototype.setLevel = function (e) {
                (this._userInfoStruct.level = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_Cur_Level, e));
              }),
              (e.prototype.getExp = function () {
                return this._userInfoStruct.exp;
              }),
              (e.prototype.getLevelUpExp = function () {
                var e = c.default
                  .getInstance()
                  .getTools()
                  .getLevelUpgradeExpJson().infos[
                  this._userInfoStruct.level - 1
                ];
                if (e) return e.levelUpExp;
              }),
              (e.prototype.setExp = function (e) {
                if (this.isMyself()) {
                  var t = c.default
                      .getInstance()
                      .getTools()
                      .getLevelUpgradeExpJson(),
                    n = t.infos[t.infos.length - 1],
                    o = t.infos[this._userInfoStruct.level - 1];
                  o &&
                    (o == n
                      ? (e > o.levelUpExp && (e = o.levelUpExp),
                        (this._userInfoStruct.exp = e))
                      : e >= o.levelUpExp
                      ? ((this._userInfoStruct.exp = e - o.levelUpExp),
                        this.setLevel(this._userInfoStruct.level + 1))
                      : (this._userInfoStruct.exp = e),
                    cc.director.emit(
                      a.GameEvent.Update_Cur_Exp,
                      e,
                      o.levelUpExp
                    ),
                    this.saveUserInfo());
                }
              }),
              (e.prototype.getHeadPhotoIdx = function () {
                return this._userInfoStruct.headPhotoIdx;
              }),
              (e.prototype.setHeadPhotoIdx = function (e) {
                (this._userInfoStruct.headPhotoIdx = e),
                  this.isMyself() &&
                    (this.saveUserInfo(),
                    cc.director.emit(a.GameEvent.Update_HeadPhoto, e));
              }),
              (e.prototype.setRobot = function (e) {
                this._isRobot = e;
              }),
              (e.prototype.isRobot = function () {
                return this._isRobot;
              }),
              (e.prototype.initLuck = function (e) {
                this.setLuck(e),
                  this.setActualLuck(e),
                  this.setTotalChangeLuckValue(a.LuckChangeType.Eate, 0),
                  this.setTotalChangeLuckValue(a.LuckChangeType.beEaten, 0);
              }),
              (e.prototype.setLuck = function (e) {
                (this._luckValue = e),
                  cc.director.emit(
                    a.GameEvent.Refresh_Player_Luck_Info,
                    this.getPlayerIndex(),
                    e
                  );
              }),
              (e.prototype.getLuck = function () {
                return this._luckValue;
              }),
              (e.prototype.setActualLuck = function (e) {
                this._actualLuckValue = e;
              }),
              (e.prototype.getActualLuck = function () {
                return this._actualLuckValue;
              }),
              (e.prototype.getTotalChangeLuckValue = function (e) {
                return (
                  null == this._totoalChangeLuckValues[e] &&
                    (this._totoalChangeLuckValues[e] = 0),
                  this._totoalChangeLuckValues[e]
                );
              }),
              (e.prototype.setTotalChangeLuckValue = function (e, t) {
                this._totoalChangeLuckValues[e] = t;
              }),
              (e.prototype.addTotalChangeLuckValue = function (e, t) {
                var n = this.getTotalChangeLuckValue(e);
                this.setTotalChangeLuckValue(e, n + t);
              }),
              (e.prototype.getPlayerIndex = function () {
                return this._userInfoStruct.playerIndex;
              }),
              (e.prototype.setPlayerIndex = function (e) {
                this._userInfoStruct.playerIndex = e;
              }),
              (e.prototype.saveUserInfo = function () {
                i.default.saveData(
                  a.DataSaveKey.User_Info,
                  JSON.stringify(this._userInfoStruct)
                );
              }),
              e
            );
          })();
        n.UserInfo = p;
        var f = (function () {
          function e() {
            (this._myselfUserInfo = null),
              (this._userInfos = []),
              (this._hasLocalUserInfo = !1),
              (this._localuserInfo = []),
              (this._customDataInfo = {
                gameTotalRounds: 0,
                watchADCount: 0,
                winRounds: 0,
                isPopupNoviceTips: !1,
              }),
              (this._signInfo = {
                date: "",
                continueDayIdx: 0,
                isSignToday: !1,
                isAd: !1,
              }),
              (this._signData = []),
              (this._loginInfo = { loginTime: 1, loginDayNum: 1 }),
              (this._timingboxInfo = {
                coinsADTimeStamp: 0,
                coinsADCount: 0,
                diamondsADTimeStamp: 0,
                diamondsADCount: 0,
                coinsADTotalCount: 0,
                firstGetStatus: a.RewardStatus.NotCan,
                secondGetStatus: a.RewardStatus.NotCan,
                thirdGetStatus: a.RewardStatus.NotCan,
              }),
              (this._gameSettingInfo = { musicStatus: !0, effectStatus: !0 }),
              (this._goodsInfoArray = []),
              (this._vasShopInfo = []),
              (this._turntableInfo = {
                timeStamp: 0,
                leftSpinCount: o.TURNTABLE_LEFT_SPIN_COUNT,
                adbonus: o.TURNTABLE_ADBONUS,
                day: "2000-1-1",
              }),
              (this._gameDifficultyInfo = {
                gameDifficulty: a.GameDifficulty.Esay,
                resultHistories: [],
              }),
              (this._cloudControlCfgInfo = {}),
              (this._luckInfo = { luck: 0 }),
              (this._onlineTime = 0),
              (this._skinInfo = { selectSkin: "original", skinBuyStatus: {} }),
              (this._shopSkinInfo = {}),
              (this._skinItemNum = 0),
              (this._IsEnterGame = 0),
              (this._isCompletedGuide = !1),
              (this._getGoldCount = 0),
              (this._languageType = a.LanguageType.English),
              (this._continuityLostCount = 0),
              (this._gameVersion = 2900),
              (this._gameCount = 0),
              (this._activityRewardCount = 5),
              (this._moneyStr = ""),
              (this._activityRewardMoney = 0),
              (this._activityprogress = 0),
              (this._showQuickGuide = !0),
              (this._showClassiceGuide = !0),
              (this._timeRewardEndTime = 0),
              (this.goldPos = null),
              (this.diaPos = null),
              (this.TurntableInfo = {
                isCanFree: !0,
                showLucky: !1,
                spinTime: 0,
                day: "",
              }),
              this.loadCloudControlCfgInfo(),
              this.loadMyselfUserInfo(),
              this.loadSignInfo(),
              this.loadTimingBoxInfo(),
              this.loadGameSettingInfo(),
              this.loadTurntableInfo(),
              this.loadGoodsInfo(),
              this.loadCustomDataInfo(),
              this.loadGameDifficultyInfo(),
              this.loadLuckInfo(),
              this.loadSkinInfo(),
              this.loadShopSkinInfo(),
              this.loadLoginInfo(),
              this.loadContinuityLostCount();
          }
          return (
            (e.getInstance = function () {
              return e._instance || (e._instance = new e()), e._instance;
            }),
            (e.prototype.getMyselfUserInfo = function () {
              return this._myselfUserInfo;
            }),
            (e.prototype.genMyselfUserId = function () {
              var e = r.default.randomOneUserId();
              this._myselfUserInfo.setUserId(e),
                this._myselfUserInfo.setNickName("Guest" + e.substring(0, 4)),
                (this._hasLocalUserInfo = !0);
            }),
            (e.prototype.genOneUserInfo = function (e) {
              return new p(
                e || {
                  userId: "",
                  nickName: "",
                  countryCode: "",
                  goldNum: 3e3,
                  diamondNum: 0,
                  level: 1,
                  exp: 0,
                  headPhotoIdx: 13,
                  playerIndex: 0,
                }
              );
            }),
            (e.prototype.hasLocalUserInfo = function () {
              return this._hasLocalUserInfo;
            }),
            (e.prototype.loadMyselfUserInfo = function () {
              var e = i.default.getData(a.DataSaveKey.User_Info);
              if ("" == e)
                (this._hasLocalUserInfo = !1),
                  (this._myselfUserInfo = this.genOneUserInfo());
              else {
                this._hasLocalUserInfo = !0;
                var t = JSON.parse(e);
                this._myselfUserInfo = this.genOneUserInfo(t);
              }
            }),
            (e.prototype.addUser = function (e) {
              this.getUser(e.getUserId()) || this._userInfos.push(e),
                cc.log("UserInfoManager addUser error, user is exist !");
            }),
            (e.prototype.getUser = function (e) {
              for (var t = 0; t < this._userInfos.length; t++)
                if (this._userInfos[t].getUserId() == e)
                  return this._userInfos[t];
              return null;
            }),
            (e.prototype.getUserByIndex = function (e) {
              for (var t = 0; t < this._userInfos.length; t++)
                if (this._userInfos[t].getPlayerIndex() == e)
                  return this._userInfos[t];
            }),
            (e.prototype.getAllUser = function () {
              return this._userInfos;
            }),
            (e.prototype.getLocalAllUser = function () {
              return this._localuserInfo;
            }),
            (e.prototype.getOhterUser = function () {
              for (var e = [], t = 0; t < this._userInfos.length; t++)
                this._userInfos[t].isMyself() || e.push(this._userInfos[t]);
              return e;
            }),
            (e.prototype.removeUser = function (e) {
              for (var t = 0; t < this._userInfos.length; t++)
                if (this._userInfos[t].getUserId() == e) {
                  this._userInfos.splice(t, 1);
                  break;
                }
            }),
            (e.prototype.generateGameUser = function () {
              var e = this,
                t = c.default.getInstance().getTools().getRobotJson().robots,
                n = function (t) {
                  for (var n = 0; n < e._userInfos.length; n++)
                    if (e._userInfos[n].getUserId() == t) return !0;
                  return !1;
                },
                i = function () {
                  var e = "";
                  do {
                    e = r.default.randomOneUserId();
                  } while (n(e));
                  return e;
                },
                s = function (t) {
                  for (var n = 0; n < e._userInfos.length; n++)
                    if (e._userInfos[n].getNickName() == t) return !0;
                  return !1;
                },
                l = function () {
                  var e = "";
                  do {
                    e = t[r.default.getRandomNum(0, t.length - 1)];
                  } while (s(e));
                  return e;
                };
              this._myselfUserInfo.setPlayerIndex(a.PlayerIndex.LeftBottom),
                this._userInfos.push(this._myselfUserInfo),
                this._myselfUserInfo.initLuck(this._luckInfo.luck);
              for (
                var d = u.default.getInstance().getEntryGold(),
                  p = c.default
                    .getInstance()
                    .getTools()
                    .getGameDifficultyJson(),
                  f = u.default.getInstance().getPlayerCount(),
                  h = u.default.getInstance().getGameMode(),
                  g = 0;
                g < f - 1;
                g++
              ) {
                var m = this.genOneUserInfo(),
                  _ = i();
                m.setUserId(_),
                  h == a.GameMode.Computer
                    ? m.setNickName("Computer")
                    : h == a.GameMode.Local
                    ? m.setNickName("Player" + (g + 2))
                    : m.setNickName(l());
                var y = r.default.getRandomNum(2e4, 5e4);
                (y += d),
                  m.setGoldNum(y),
                  m.setDiamondNum(r.default.getRandomNum(0, 200)),
                  f == a.PlayerCount.Two
                    ? m.setPlayerIndex(a.PlayerIndex.RightTop)
                    : m.setPlayerIndex(g + 1),
                  m.setHeadPhotoIdx(this.getPhotoIndex(g)),
                  m.setRobot(!0),
                  m.setCountryCode(
                    r.default
                      .getRandomNum(0, o.PLAYER_HEAD_PHOTO_COUNT - 1)
                      .toString()
                  ),
                  m.initLuck(p.luckInit),
                  this._userInfos.push(m);
              }
            }),
            (e.prototype.getPhotoIndex = function (e) {
              var t = [1, 3, 5, 7, 10, 13, 15, 16];
              return e > 2
                ? t[r.default.getRandomNum(1, t.length) - 1]
                : r.default.getRandomNum(1, t.length);
            }),
            (e.prototype.localGenerateGameUser = function () {
              var e = this,
                t = function (t) {
                  for (var n = 0; n < e._localuserInfo.length; n++)
                    if (e._localuserInfo[n].getUserId() == t) return !0;
                  return !1;
                },
                n = function () {
                  var e = "";
                  do {
                    e = r.default.randomOneUserId();
                  } while (t(e));
                  return e;
                };
              this._myselfUserInfo.setPlayerIndex(a.PlayerIndex.LeftBottom),
                this._localuserInfo.push(this._myselfUserInfo),
                this._myselfUserInfo.initLuck(this._luckInfo.luck);
              var i = u.default.getInstance().getEntryGold(),
                s = c.default.getInstance().getTools().getGameDifficultyJson(),
                l = c.default.getInstance().getLocalInfo(),
                d = ["game_bule", "game_red", "game_green", "game_yellow"];
              for (var p in l)
                if (0 != parseInt(p)) {
                  var f = this.genOneUserInfo(),
                    h = n();
                  f.setUserId(h), f.setNickName(d[p]);
                  var g = r.default.getRandomNum(5e3, 5e4);
                  (g += i),
                    f.setGoldNum(g),
                    f.setDiamondNum(r.default.getRandomNum(0, 200)),
                    f.setPlayerIndex(parseInt(p)),
                    f.setHeadPhotoIdx(
                      r.default.getRandomNum(1, o.PLAYER_HEAD_PHOTO_COUNT)
                    ),
                    f.setRobot(l[p].isComputer),
                    f.setCountryCode(
                      r.default
                        .getRandomNum(0, o.PLAYER_HEAD_PHOTO_COUNT - 1)
                        .toString()
                    ),
                    f.initLuck(s.luckInit),
                    this._localuserInfo.push(f);
                }
            }),
            (e.prototype.addPlayer = function (e) {
              var t = this,
                n = function (e) {
                  for (var n = 0; n < t._localuserInfo.length; n++)
                    if (t._localuserInfo[n].getUserId() == e) return !0;
                  return !1;
                },
                a = c.default.getInstance().getTools().getGameDifficultyJson(),
                i = this.genOneUserInfo(),
                s = (function () {
                  var e = "";
                  do {
                    e = r.default.randomOneUserId();
                  } while (n(e));
                  return e;
                })();
              i.setUserId(s), i.setNickName("Player" + (e + 1));
              var l = r.default.getRandomNum(2e4, 5e4);
              (l += 1),
                i.setGoldNum(l),
                i.setDiamondNum(r.default.getRandomNum(0, 200)),
                i.setPlayerIndex(e),
                i.setHeadPhotoIdx(
                  r.default.getRandomNum(1, o.PLAYER_HEAD_PHOTO_COUNT)
                ),
                i.setRobot(!1),
                i.setCountryCode(
                  r.default
                    .getRandomNum(0, o.PLAYER_HEAD_PHOTO_COUNT - 1)
                    .toString()
                ),
                i.initLuck(a.luckInit),
                this._localuserInfo.push(i);
            }),
            (e.prototype.delPlayer = function (e) {
              for (var t = 0; t < this._localuserInfo.length; t++)
                if (this._localuserInfo[t].getPlayerIndex() == e) {
                  this._localuserInfo.splice(t, 1);
                  break;
                }
            }),
            (e.prototype.deductEntryGold = function () {
              i.default.nativeLog("\u6263\u94b1\u4e86");
              var e = u.default.getInstance().getEntryGold();
              e &&
                s.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: a.BuriedOneKey.goldCostCount,
                    actionName: a.BuriedTwoKey.goldCostOnline,
                    value: e,
                  });
              for (var t = 0; t < this._userInfos.length; t++) {
                var n = this._userInfos[t],
                  o = n.getGoldNum();
                o >= e && n.setGoldNum(o - e);
              }
            }),
            (e.prototype.copyValue = function (e, t) {
              for (var n in t)
                null != e[n] &&
                  ("object" == typeof e[n]
                    ? this.copyValue(e[n], t[n])
                    : (t[n] = e[n]));
            }),
            (e.prototype.setDataByLocal = function (e, t) {
              this.copyValue(e, t);
            }),
            (e.prototype.loadActivityRewardCount = function () {
              var e = i.default.getData(a.DataSaveKey.ActivityRewardCount),
                t = this.getOpenActivityTime(),
                n = r.default.getDateString();
              if (r.default.getDiffDay(t, n)) {
                var o = c.default.getInstance().getTools().getGlobalJson()
                  .info[0].activityRewardCount;
                this._activityRewardCount = o;
              } else e && (this._activityRewardCount = JSON.parse(e));
              this.setActivityRewardCount(this._activityRewardCount);
            }),
            (e.prototype.setActivityRewardCount = function (e) {
              (this._activityRewardCount = e),
                i.default.saveData(
                  a.DataSaveKey.ActivityRewardCount,
                  JSON.stringify(this._activityRewardCount)
                );
            }),
            (e.prototype.getActivityRewardCount = function () {
              return this._activityRewardCount;
            }),
            (e.prototype.setOpenActivityTime = function () {
              var e = r.default.getDateString();
              i.default.saveData(
                a.DataSaveKey.OpenActivityTime,
                JSON.stringify(e)
              );
            }),
            (e.prototype.getOpenActivityTime = function () {
              var e = i.default.getData(a.DataSaveKey.OpenActivityTime);
              return e ? JSON.parse(e) : 0;
            }),
            (e.prototype.loadSignInfo = function () {
              var e = i.default.getData(a.DataSaveKey.Sign_Info);
              console.log("strSignInfo: " + e),
                "" != e && this.setDataByLocal(JSON.parse(e), this._signInfo),
                this.setSignData();
            }),
            (e.prototype.setSignData = function () {
              (this._signData = []), console.log("setSignData: ");
              var e = c.default.getInstance().getTools().getSignJson().rewards;
              if ("" == this._signInfo.date) {
                console.log(
                  "set\u7b7e\u5230\u6570\u636e\uff1athis._signInfo.date\uff1a " +
                    this._signInfo.date +
                    "this._signInfo.continueDayIdx: " +
                    this._signInfo.continueDayIdx +
                    "this._signInfo.isSignToday" +
                    this._signInfo.isSignToday +
                    "this._signInfo.isAd: " +
                    this._signInfo.isAd
                );
                for (var t = 1; t <= 7; t++) {
                  var n = {
                    dayIndex: t - 1,
                    status: a.RewardStatus.NotCan,
                    coins: e[t - 1].coins,
                  };
                  1 == t && (n.status = a.RewardStatus.Can),
                    this._signData.push(n),
                    console.log("this._signData000000: " + this._signData);
                }
              } else {
                var o = r.default.getDiffDay(
                  r.default.getDateString(),
                  this._signInfo.date
                );
                if ((console.log("diffDay: " + o), 1 == o || 0 == o)) {
                  var i = this._signInfo.continueDayIdx;
                  for (
                    1 == o
                      ? ((i += 1),
                        (this._signInfo.isSignToday = !1),
                        (this._signInfo.isAd = !1))
                      : (this._signInfo.isSignToday = !0),
                      t = 1;
                    t <= 7;
                    t++
                  )
                    (n = {
                      dayIndex: t - 1,
                      status: a.RewardStatus.NotCan,
                      coins: e[t - 1].coins,
                    }),
                      t < i
                        ? (n.status = a.RewardStatus.Got)
                        : t == i
                        ? this._signInfo.isSignToday
                          ? (n.status = a.RewardStatus.Got)
                          : (n.status = a.RewardStatus.Can)
                        : (n.status = a.RewardStatus.NotCan),
                      this._signData.push(n);
                  console.log("this._signData11111: " + this._signData);
                } else if (o > 1) {
                  for (
                    this._signInfo.continueDayIdx = 0,
                      this._signInfo.isSignToday = !1,
                      this._signInfo.isAd = !1,
                      t = 1;
                    t <= 7;
                    t++
                  )
                    (n = {
                      dayIndex: t - 1,
                      status: a.RewardStatus.NotCan,
                      coins: e[t - 1].coins,
                    }),
                      1 == t && (n.status = a.RewardStatus.Can),
                      this._signData.push(n);
                  console.log("this._signData222222: " + this._signData);
                }
              }
            }),
            (e.prototype.getSignData = function () {
              return this._signData;
            }),
            (e.prototype.getSignInfo = function () {
              return this._signInfo;
            }),
            (e.prototype.setSignInfo = function (e, t, n, o) {
              null != e && (this._signInfo.date = e),
                null != t && (this._signInfo.continueDayIdx = t),
                null != n && (this._signInfo.isSignToday = n),
                null != o && (this._signInfo.isAd = o),
                this.setSignData(),
                console.log(
                  "set\u7b7e\u5230\u6570\u636e\uff1athis._signInfo.date\uff1a " +
                    this._signInfo.date +
                    "this._signInfo.continueDayIdx: " +
                    this._signInfo.continueDayIdx +
                    "this._signInfo.isSignToday" +
                    this._signInfo.isSignToday +
                    "this._signInfo.isAd: " +
                    this._signInfo.isAd
                ),
                i.default.saveData(
                  a.DataSaveKey.Sign_Info,
                  JSON.stringify(this._signInfo)
                );
            }),
            (e.prototype.loadTimingBoxInfo = function () {
              var e = i.default.getData(a.DataSaveKey.TimingBox_Info);
              if ("" != e) {
                this.setDataByLocal(JSON.parse(e), this._timingboxInfo);
                var t,
                  n = r.default.getCurTimeStamp();
                if (0 != this._timingboxInfo.coinsADTimeStamp)
                  if (
                    (t = Math.floor(
                      (n - this._timingboxInfo.coinsADTimeStamp) / 1e3
                    )) < o.TIMINGBOX_REFRESH_TIME
                  ) {
                    var s = o.TIMINGBOX_REFRESH_TIME - t;
                    l.default.getInstance().startTimingBoxCoinsTimer(s);
                  } else
                    this.setTimingBoxInfo(0, 0, null, null, null, null, null);
                0 != this._timingboxInfo.diamondsADTimeStamp &&
                  ((t = Math.floor(
                    (n - this._timingboxInfo.diamondsADTimeStamp) / 1e3
                  )) < o.TIMINGBOX_REFRESH_TIME
                    ? ((s = o.TIMINGBOX_REFRESH_TIME - t),
                      l.default.getInstance().startTimingBoxDiamondsTimer(s))
                    : this.setTimingBoxInfo(
                        null,
                        null,
                        0,
                        0,
                        null,
                        null,
                        null
                      ));
              }
            }),
            (e.prototype.getTimingBoxInfo = function () {
              return this._timingboxInfo;
            }),
            (e.prototype.setTimingBoxRewardStatus = function () {
              for (
                var e = [
                    this._timingboxInfo.firstGetStatus,
                    this._timingboxInfo.secondGetStatus,
                    this._timingboxInfo.thirdGetStatus,
                  ],
                  t = c.default
                    .getInstance()
                    .getTools()
                    .getTimingBoxRewardJson().rewards,
                  n = 0;
                n < t.length;
                n++
              )
                e[n] == a.RewardStatus.NotCan &&
                  t[n].count <= this._timingboxInfo.coinsADTotalCount &&
                  (0 == n
                    ? (this._timingboxInfo.firstGetStatus = a.RewardStatus.Can)
                    : 1 == n
                    ? (this._timingboxInfo.secondGetStatus = a.RewardStatus.Can)
                    : 2 == n &&
                      (this._timingboxInfo.thirdGetStatus =
                        a.RewardStatus.Can));
            }),
            (e.prototype.setTimingBoxInfo = function (e, t, n, o, r, s, c) {
              null != e && (this._timingboxInfo.coinsADTimeStamp = e),
                null != t &&
                  ((this._timingboxInfo.coinsADCount = t),
                  0 != t &&
                    ((this._timingboxInfo.coinsADTotalCount += 1),
                    this.setTimingBoxRewardStatus())),
                null != n && (this._timingboxInfo.diamondsADTimeStamp = n),
                null != o && (this._timingboxInfo.diamondsADCount = o),
                null != r && (this._timingboxInfo.firstGetStatus = r),
                null != s && (this._timingboxInfo.secondGetStatus = s),
                null != c && (this._timingboxInfo.thirdGetStatus = c),
                i.default.saveData(
                  a.DataSaveKey.TimingBox_Info,
                  JSON.stringify(this._timingboxInfo)
                );
            }),
            (e.prototype.loadGameSettingInfo = function () {
              var e = i.default.getData(a.DataSaveKey.GameSetting_Info);
              "" != e &&
                this.setDataByLocal(JSON.parse(e), this._gameSettingInfo);
            }),
            (e.prototype.getGameSettingInfo = function () {
              return this._gameSettingInfo;
            }),
            (e.prototype.setGameSettingInfo = function (e, t) {
              null != e && (this._gameSettingInfo.musicStatus = e),
                null != t && (this._gameSettingInfo.effectStatus = t),
                i.default.saveData(
                  a.DataSaveKey.GameSetting_Info,
                  JSON.stringify(this._gameSettingInfo)
                );
            }),
            (e.prototype.loadGoodsInfo = function () {
              var e = [],
                t = i.default.getGoodsInfo();
              if ("" != t) {
                var n = JSON.parse(t);
                i.default.nativeLog("loadGoodsInfo-----goodsInfo:" + n);
                for (var o = 0; o < n.length; o++) e.push(n[o]);
                i.default.nativeLog("loadGoodsInfo-----goodsArray:" + e);
              }
              var a = [],
                r = i.default.getVasPayInfo();
              if (
                (i.default.nativeLog("vasGoodsInfo-----vasGoodsInfo:" + r),
                "" != r)
              ) {
                var s = JSON.parse(r);
                for (var o in (i.default.nativeLog(
                  "vasGoodsInfo1-----vasGoodsInfo1:" + s
                ),
                s))
                  a.push(s[o]);
              }
              (this._vasShopInfo = a), (this._goodsInfoArray = e);
            }),
            (e.prototype.getGoodsInfo = function () {
              return (
                i.default.nativeLog(
                  "this._goodsInfoArray" + this._goodsInfoArray
                ),
                this._goodsInfoArray
              );
            }),
            (e.prototype.getVasShopInfo = function () {
              return this._vasShopInfo;
            }),
            (e.prototype.loadTurntableInfo = function () {
              var e = i.default.getData(a.DataSaveKey.newTurntableInfo);
              if ("" != e) {
                this.setDataByLocal(JSON.parse(e), this.TurntableInfo);
                var t = r.default.getCurTimeStamp(),
                  n = r.default.getDateString(),
                  s = r.default.getDiffDay(this.TurntableInfo.day, n);
                0 != this.TurntableInfo.spinTime
                  ? (Math.floor((t - this.TurntableInfo.spinTime) / 1e3) >
                      o.TURNTABLE_CD_TIME &&
                      this.setNewTurntableInfo(!1, !0, 0, ""),
                    s > 0 && this.setNewTurntableInfo(!0, !1, 0, ""))
                  : s > 0 && this.setNewTurntableInfo(!0, !1, 0, "");
              }
            }),
            (e.prototype.setNewTurntableInfo = function (e, t, n, o) {
              (this.TurntableInfo.isCanFree = e),
                (this.TurntableInfo.showLucky = t),
                (this.TurntableInfo.spinTime = n),
                (this.TurntableInfo.day = o),
                i.default.saveData(
                  a.DataSaveKey.newTurntableInfo,
                  JSON.stringify(this.TurntableInfo)
                );
            }),
            (e.prototype.getNewTurntableInfo = function () {
              return this.TurntableInfo;
            }),
            (e.prototype.getTurntableInfo = function () {
              return this._turntableInfo;
            }),
            (e.prototype.setTurntableInfo = function (e, t, n, o) {
              void 0 === o && (o = !1),
                null != e && (this._turntableInfo.timeStamp = e),
                null != t && (this._turntableInfo.leftSpinCount = t),
                null != n && (this._turntableInfo.adbonus = n > 0 ? n : 0),
                (this._turntableInfo.day = r.default.getDateString()),
                i.default.saveData(
                  a.DataSaveKey.Turntable_Info,
                  JSON.stringify(this._turntableInfo)
                );
            }),
            (e.prototype.loadCustomDataInfo = function () {
              var e = i.default.getData(a.DataSaveKey.CustomData_Info);
              "" != e &&
                this.setDataByLocal(JSON.parse(e), this._customDataInfo);
            }),
            (e.prototype.getCustomDataInfo = function () {
              return this._customDataInfo;
            }),
            (e.prototype.setCustomDataInfo = function (e, t, n, o) {
              null != e && (this._customDataInfo.gameTotalRounds = e),
                null != t && (this._customDataInfo.watchADCount = t),
                null != n && (this._customDataInfo.winRounds = n),
                null != o && (this._customDataInfo.isPopupNoviceTips = o),
                i.default.saveData(
                  a.DataSaveKey.CustomData_Info,
                  JSON.stringify(this._customDataInfo)
                );
            }),
            (e.prototype.addGameTotalRounds = function () {
              this.setCustomDataInfo(
                this._customDataInfo.gameTotalRounds + 1,
                null,
                null,
                null
              );
            }),
            (e.prototype.getGameTotalRounds = function () {
              return this._customDataInfo.gameTotalRounds;
            }),
            (e.prototype.addWatchADCount = function () {
              this.setCustomDataInfo(
                null,
                this._customDataInfo.watchADCount + 1,
                null,
                null
              );
            }),
            (e.prototype.addWinRounds = function () {
              this.setCustomDataInfo(
                null,
                null,
                this._customDataInfo.winRounds + 1,
                null
              );
            }),
            (e.prototype.loadGameDifficultyInfo = function () {
              var e = i.default.getData(a.DataSaveKey.GameDifficulty_Info);
              "" != e &&
                this.setDataByLocal(JSON.parse(e), this._gameDifficultyInfo);
            }),
            (e.prototype.loadShopSkinInfo = function () {
              var e = i.default.getData(a.DataSaveKey.Shop_Skin_Info);
              if (e) {
                var t = JSON.parse(e);
                for (var n in t) null != t[n] && (this._shopSkinInfo[n] = t[n]);
              }
            }),
            (e.prototype.setShopSkinInfo = function (e, t, n) {
              var o = { id: 0, adCount: 0, endTime: 0 };
              e && ((o[e] = e), (o.id = e)),
                t && (o.adCount = t),
                n && (o.endTime = n),
                (this._shopSkinInfo[e] = o),
                i.default.saveData(
                  a.DataSaveKey.Shop_Skin_Info,
                  JSON.stringify(this._shopSkinInfo)
                );
              var r = d.default.getInstance().getSkinInfo(e);
              cc.director.emit(a.GameEvent.Update_Ad_Skin, r);
            }),
            (e.prototype.getShopSkinInfo = function (e) {
              var t = null;
              return this._shopSkinInfo[e] && (t = this._shopSkinInfo[e]), t;
            }),
            (e.prototype.getShopSkinList = function () {
              return this._shopSkinInfo;
            }),
            (e.prototype.setGameDifficultyInfo = function (e, t) {
              null != e && (this._gameDifficultyInfo.gameDifficulty = e),
                null != t && this._gameDifficultyInfo.resultHistories.push(t),
                i.default.saveData(
                  a.DataSaveKey.GameDifficulty_Info,
                  JSON.stringify(this._gameDifficultyInfo)
                );
            }),
            (e.prototype.getGameDifficultyInfo = function () {
              return this._gameDifficultyInfo;
            }),
            (e.prototype.getContinueResult = function () {
              if (this._gameDifficultyInfo.resultHistories.length > 0) {
                for (
                  var e = 0,
                    t = this._gameDifficultyInfo.resultHistories.length - 1,
                    n = this._gameDifficultyInfo.resultHistories[t],
                    o = t;
                  o >= 0 && this._gameDifficultyInfo.resultHistories[o] == n;
                  o--
                )
                  e += 1;
                return { result: n, continueCount: e };
              }
            }),
            (e.prototype.clearResultHistories = function () {
              (this._gameDifficultyInfo.resultHistories = []),
                i.default.saveData(
                  a.DataSaveKey.GameDifficulty_Info,
                  JSON.stringify(this._gameDifficultyInfo)
                );
            }),
            (e.prototype.loadCloudControlCfgInfo = function () {
              (this._cloudControlCfgInfo[
                a.CloudControlConfigKey.GameDifficulty
              ] = i.default.getCloudControlConfig(
                a.CloudControlConfigKey.GameDifficulty
              )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.GameProps] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.GameProps
                  )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.LevelExp] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.LevelExp
                  )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.EntryCoins] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.EntryCoins
                  )),
                (this._cloudControlCfgInfo[
                  a.CloudControlConfigKey.TimingBoxReward
                ] = i.default.getCloudControlConfig(
                  a.CloudControlConfigKey.TimingBoxReward
                )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.Shop] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.Shop
                  )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.Task] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.Task
                  )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.Global] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.Global
                  )),
                (this._cloudControlCfgInfo[a.CloudControlConfigKey.GameInfo] =
                  i.default.getCloudControlConfig(
                    a.CloudControlConfigKey.GameInfo
                  ));
            }),
            (e.prototype.getCloudControlCfg = function (e) {
              return this._cloudControlCfgInfo[e];
            }),
            (e.prototype.loadLuckInfo = function () {
              var e = this,
                t = i.default.getData(a.DataSaveKey.Luck_Info);
              "" != t
                ? this.setDataByLocal(JSON.parse(t), this._luckInfo)
                : setTimeout(function () {
                    var t = c.default
                      .getInstance()
                      .getTools()
                      .getGameDifficultyJson();
                    e._luckInfo.luck = t.luckInit;
                  }, 0.5);
            }),
            (e.prototype.getLuckInfo = function () {
              return this._luckInfo;
            }),
            (e.prototype.setLuckInfo = function (e) {
              null != e && (this._luckInfo.luck = e),
                i.default.saveData(
                  a.DataSaveKey.Luck_Info,
                  JSON.stringify(this._luckInfo)
                );
            }),
            (e.prototype.loadSkinInfo = function () {
              var e = i.default.getData(a.DataSaveKey.Skin_Info);
              "" != e && (this._skinInfo = JSON.parse(e));
              var t = i.default.getData(a.DataSaveKey.Skin_Item);
              "" != t && (this._skinItemNum = JSON.parse(t));
            }),
            (e.prototype.getSkinInfo = function () {
              return this._skinInfo;
            }),
            (e.prototype.setSkinInfo = function (e, t, n, o) {
              if (
                (void 0 === o && (o = 0),
                null != e && (this._skinInfo.selectSkin = e),
                null != t && null != n)
              ) {
                var r = { buyStatus: 0, endTime: 0 };
                (r.buyStatus = n),
                  n == a.BuyStatus.Experience && (r.endTime = o),
                  (this._skinInfo.skinBuyStatus[t] = r);
              }
              i.default.saveData(
                a.DataSaveKey.Skin_Info,
                JSON.stringify(this._skinInfo)
              );
            }),
            (e.prototype.getSkinEndTime = function (e, t) {
              var n = null;
              for (var o in this._skinInfo)
                if (
                  this._skinInfo.selectSkin == e &&
                  this._skinInfo.skinBuyStatus[t] != a.BuyStatus.Purchased
                ) {
                  n = this._skinInfo;
                  break;
                }
              return n && "" != n.skinBuyStatus[t].endTime
                ? n.skinBuyStatus[t].endTime
                : r.default.getCurTimeStamp();
            }),
            (e.prototype.setOfflineTime = function () {
              var e = r.default.getDateString();
              i.default.saveData(
                a.DataSaveKey.Offline_Time_Info,
                JSON.stringify(e)
              );
            }),
            (e.prototype.setOnlineTime = function (e) {
              e ? (this._onlineTime = e) : (this._onlineTime += 5),
                i.default.saveData(
                  a.DataSaveKey.Online_Time_Info,
                  JSON.stringify(this._onlineTime)
                );
            }),
            (e.prototype.setIsEnterGame = function (e) {
              (this._IsEnterGame = e),
                i.default.saveData(
                  a.DataSaveKey.IsEnterGame,
                  JSON.stringify(this._IsEnterGame)
                );
            }),
            (e.prototype.getIsEnterGame = function () {
              var e = i.default.getData(a.DataSaveKey.IsEnterGame);
              return (
                e && (this._IsEnterGame = JSON.parse(e)), this._IsEnterGame
              );
            }),
            (e.prototype.getOnlineTime = function () {
              var e = i.default.getData(a.DataSaveKey.Online_Time_Info);
              return "" != e ? parseInt(JSON.parse(e)) : 0;
            }),
            (e.prototype.setSkinItemNum = function (e) {
              (this._skinItemNum = e),
                i.default.saveData(
                  a.DataSaveKey.Skin_Item,
                  JSON.stringify(this._skinItemNum)
                ),
                cc.director.emit(
                  a.GameEvent.Update_Skin_Num,
                  this._skinItemNum
                );
            }),
            (e.prototype.getSkinItem = function () {
              return this._skinItemNum;
            }),
            (e.prototype.clearData = function () {
              (this._userInfos = []),
                c.default.getInstance().getIsAgain() ||
                  (this._localuserInfo = []);
            }),
            (e.prototype.setCompletedGuide = function (e) {
              (this._isCompletedGuide = e),
                i.default.saveData(
                  a.DataSaveKey.IsCompletedGuide,
                  JSON.stringify(this._isCompletedGuide)
                );
            }),
            (e.prototype.getCompletedGuide = function () {
              var e = i.default.getData(a.DataSaveKey.IsCompletedGuide);
              return (
                e && (this._isCompletedGuide = JSON.parse(e)),
                this._isCompletedGuide
              );
            }),
            (e.prototype.getGoldCount = function () {
              var e = i.default.getData(a.DataSaveKey.GetGoldCount);
              return (
                e && (this._getGoldCount = JSON.parse(e)), this._getGoldCount
              );
            }),
            (e.prototype.setGoldCount = function () {
              this._getGoldCount++,
                i.default.saveData(
                  a.DataSaveKey.GetGoldCount,
                  JSON.stringify(this._getGoldCount)
                );
            }),
            (e.prototype.getLanguage = function () {
              var e = i.default.getData(a.DataSaveKey.Language_Type);
              return (
                console.log("_languageType: " + e),
                e && (this._languageType = JSON.parse(e)),
                this._languageType
              );
            }),
            (e.prototype.setLanguage = function (e) {
              (this._languageType = e),
                i.default.saveData(
                  a.DataSaveKey.Language_Type,
                  JSON.stringify(this._languageType)
                );
            }),
            (e.prototype.getAppLanguage = function () {
              console.log("\u6e38\u620f\u542f\u52a8");
              var e = i.default.getLanguageStr();
              e &&
                ("US" == e
                  ? (this._languageType = a.LanguageType.English)
                  : "IN" == e
                  ? (this._languageType = a.LanguageType.Hindi)
                  : "PK" == e
                  ? (this._languageType = a.LanguageType.Urdu)
                  : ("DZ" != e &&
                      "EG" != e &&
                      "LY" != e &&
                      "MA" != e &&
                      "TN" != e &&
                      "SA" != e) ||
                    (this._languageType = a.LanguageType.Arabic)),
                i.default.saveData(
                  a.DataSaveKey.Language_Type,
                  JSON.stringify(this._languageType)
                );
            }),
            (e.prototype.isShowAppluck = function (e) {
              if (e) {
                var t = i.default.getLanguageStr();
                ("US" != t &&
                  "BR" != t &&
                  "ID" != t &&
                  "IN" != t &&
                  "PH" != t &&
                  "MX" != t) ||
                  i.default.showAppluck();
              } else console.log("hideAppluck"), i.default.hideAppluck();
            }),
            (e.prototype.getContinuityLostCount = function () {
              return this._continuityLostCount;
            }),
            (e.prototype.setContinuityLostCount = function (e) {
              (this._continuityLostCount = e),
                i.default.saveData(
                  a.DataSaveKey.ContinuityLostCount,
                  JSON.stringify(this._continuityLostCount)
                );
            }),
            (e.prototype.loadContinuityLostCount = function () {
              var e = i.default.getData(a.DataSaveKey.ContinuityLostCount);
              e && (this._continuityLostCount = JSON.parse(e));
            }),
            (e.prototype.loadLoginInfo = function () {
              var e = i.default.getData(a.DataSaveKey.Login_Info);
              if (e) {
                var t = JSON.parse(e),
                  n = r.default.getCurTimeStamp(),
                  o = new Date(n),
                  s = new Date(t.loginTime);
                o.getDay() != s.getDay() &&
                  (this._loginInfo.loginDayNum = t.loginDayNum + 1),
                  (this._loginInfo.loginTime = n);
              }
              i.default.saveData(
                a.DataSaveKey.Login_Info,
                JSON.stringify(this._loginInfo)
              );
            }),
            (e.prototype.getLoginDayNum = function () {
              return this._loginInfo.loginDayNum;
            }),
            (e.prototype.setGameCount = function (e) {
              (this._gameCount = e),
                i.default.saveData(
                  a.DataSaveKey.GameCount,
                  JSON.stringify(this._gameCount)
                );
            }),
            (e.prototype.getGameCount = function () {
              return this._gameCount;
            }),
            (e.prototype.setGameVersion = function (e) {
              (this._gameVersion = e),
                i.default.saveData(
                  a.DataSaveKey.GameVersion,
                  JSON.stringify(this._gameVersion)
                );
            }),
            (e.prototype.getGameVersion = function () {
              var e = i.default.getData(a.DataSaveKey.GameVersion);
              return (
                e && (this._gameVersion = JSON.parse(e)), this._gameVersion
              );
            }),
            (e.prototype.addActivityprogress = function () {
              var e;
              (e =
                0 == this._activityprogress
                  ? r.default.getActivityRandomNum(15, 20)
                  : this._activityprogress > 80 && this._activityprogress < 95
                  ? r.default.getActivityRandomNum(1, 3)
                  : this._activityprogress > 95 && this._activityprogress < 99
                  ? r.default.getActivityRandomNum(0.5, 1)
                  : this._activityprogress > 99 && this._activityprogress < 100
                  ? r.default.getActivityRandomNum(0.01, 0.04)
                  : r.default.getActivityRandomNum(10, 15)),
                console.log("\u6d3b\u52a8\u968f\u673a\u8fdb\u5ea6: " + e),
                this.setActivityRewardCount(this._activityRewardCount - 1),
                this.setActivityprogress(this._activityprogress + e);
            }),
            (e.prototype.setActivityprogress = function (e) {
              (this._activityprogress = e),
                i.default.saveData(
                  a.DataSaveKey.Activityprogress,
                  JSON.stringify(this._activityprogress)
                );
            }),
            (e.prototype.getActivityprogress = function () {
              var e = i.default.getData(a.DataSaveKey.Activityprogress);
              return (
                e && (this._activityprogress = JSON.parse(e)),
                this._activityprogress
              );
            }),
            (e.prototype.getActivityCountry = function () {
              var e = i.default.getLanguageStr(),
                t = c.default.getInstance().getTools().getGlobalJson();
              "NG" == e
                ? ((this._moneyStr = "\u20a6"),
                  (this._activityRewardMoney = t.info[0].activityNGReward))
                : "ID" == e
                ? ((this._moneyStr = "Rp"),
                  (this._activityRewardMoney = t.info[0].activityIDReward))
                : "PH" == e
                ? ((this._moneyStr = "\u20b1"),
                  (this._activityRewardMoney = t.info[0].activityPHReward))
                : ((this._moneyStr = "$"),
                  (this._activityRewardMoney = t.info[0].activityUSReward));
            }),
            (e.prototype.getMoneyStr = function () {
              return this._moneyStr;
            }),
            (e.prototype.getMoneyRewardCount = function () {
              return this._activityRewardMoney;
            }),
            (e.prototype.getQuickGuide = function () {
              var e = i.default.getData(a.DataSaveKey.Enter_Quick_Mode);
              return (
                e && (this._showQuickGuide = JSON.parse(e)),
                this._showQuickGuide
              );
            }),
            (e.prototype.setQuickGuide = function () {
              (this._showQuickGuide = !1),
                i.default.saveData(
                  a.DataSaveKey.Enter_Quick_Mode,
                  JSON.stringify(this._showQuickGuide)
                );
            }),
            (e.prototype.getClassiceGuide = function () {
              var e = i.default.getData(a.DataSaveKey.Enter_Classice_Mode);
              return (
                e && (this._showClassiceGuide = JSON.parse(e)),
                this._showClassiceGuide
              );
            }),
            (e.prototype.setClassiceGuide = function () {
              (this._showClassiceGuide = !1),
                i.default.saveData(
                  a.DataSaveKey.Enter_Classice_Mode,
                  JSON.stringify(this._showClassiceGuide)
                );
            }),
            (e.prototype.setTimeReward = function (e) {
              (this._timeRewardEndTime = e),
                i.default.saveData(
                  a.DataSaveKey.Time_Reward_End_Time,
                  JSON.stringify(this._timeRewardEndTime)
                );
            }),
            (e.prototype.getTimeReward = function () {
              var e = i.default.getData(a.DataSaveKey.Time_Reward_End_Time);
              return (
                e && (this._timeRewardEndTime = JSON.parse(e)),
                this._timeRewardEndTime
              );
            }),
            (e._instance = null),
            e
          );
        })();
        (n.default = f), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Native/NativeBridge": "NativeBridge",
        "../Utils/Utils": "Utils",
        "./BuriedPointManager": "BuriedPointManager",
        "./GameDataManager": "GameDataManager",
        "./GlobalTimerManager": "GlobalTimerManager",
        "./RoomInfoManager": "RoomInfoManager",
        "./ShopDataManager": "ShopDataManager",
      },
    ],
    UserInfoView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "6a088ww8qZHppnZqZXHjrbO", "UserInfoView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("../Framework/Utils/Utils"),
          p = e("./ModifyCountryView"),
          f = e("./ModifyHeadPhotoView"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.sprHeadPhoto = null),
                (t.labNickName = null),
                (t.sprCountry = null),
                (t.label_country = null),
                (t.labGold = null),
                (t.labExp = null),
                (t.progressExp = null),
                (t.modifyNickNameViewPrefab = null),
                (t.modifyHeadPhotoViewPrefab = null),
                (t.modifyCountryViewPrefab = null),
                (t.labWinRounds = null),
                (t.base_node = null),
                (t.img_bg = null),
                (t.edit_name = null),
                (t.label_exp = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                d.default.localStr(this.node), this.registerAllEvents();
                var e = u.default.getInstance().getMyselfUserInfo();
                this.onUpdateHeadPhoto(e.getHeadPhotoIdx()),
                  (this.edit_name.string = e.getNickName()),
                  this.onUpdateNickName(e.getNickName()),
                  this.onUpdateCountryCode(e.getCountryCode()),
                  this.onUpdateGold(e.getGoldNum()),
                  this.onUpdateExp(e.getExp(), e.getLevelUpExp(), e.getLevel()),
                  this.updateWinRounds();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  c.GameEvent.Update_HeadPhoto,
                  this.onUpdateHeadPhoto,
                  this
                ),
                  this.registerEvent(
                    c.GameEvent.Update_Nick_Name,
                    this.onUpdateNickName,
                    this
                  ),
                  this.registerEvent(
                    c.GameEvent.Update_Country_Code,
                    this.onUpdateCountryCode,
                    this
                  );
              }),
              (t.prototype.onUpdateHeadPhoto = function (e) {
                var t = this;
                this.loadRes(
                  s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + e,
                  cc.SpriteFrame,
                  function (e) {
                    t.sprHeadPhoto.spriteFrame = e;
                  }
                );
              }),
              (t.prototype.onUpdateNickName = function (e) {
                this.labNickName.string = e;
              }),
              (t.prototype.onUpdateCountryCode = function (e) {
                var t = this,
                  n = "";
                "" == e ||
                  ((n = s.PLAYER_COUNTRY_ICON_PATH + "country_icon_" + e),
                  this.loadRes(n, cc.SpriteFrame, function (e) {
                    t.sprCountry.spriteFrame = e;
                  }));
                var o = l.default.getInstance().getTools().getCountryJson();
                o.countries[e] &&
                  (this.label_country.string = o.countries[e].countryName);
              }),
              (t.prototype.onUpdateGold = function (e) {
                this.labGold.string = "" + e;
              }),
              (t.prototype.onUpdateExp = function (e, t, n) {
                (this.labExp.string = "Lv" + n),
                  (this.progressExp.progress = e / t),
                  (this.label_exp.string = e + "/" + t);
              }),
              (t.prototype.updateWinRounds = function () {
                var e = u.default.getInstance().getCustomDataInfo();
                this.labWinRounds.string = e.winRounds.toString();
              }),
              (t.prototype.onClickModifyNickName = function () {
                cc.instantiate(this.modifyNickNameViewPrefab).parent =
                  this.base_node;
              }),
              (t.prototype.onClickModifyHeadPhoto = function () {
                var e = this,
                  t = cc.instantiate(this.modifyHeadPhotoViewPrefab);
                (t.parent = this.base_node),
                  (this.img_bg.active = !1),
                  t.getComponent(f.default).setCallBack(function () {
                    e.img_bg.active = !0;
                  });
              }),
              (t.prototype.onClickModifyCountry = function () {
                var e = this,
                  t = cc.instantiate(this.modifyCountryViewPrefab);
                (t.parent = this.base_node),
                  (this.img_bg.active = !1),
                  t.getComponent(p.default).setCallBack(function () {
                    e.img_bg.active = !0;
                  });
              }),
              (t.prototype.onEditEndClick = function () {
                "" != this.edit_name.string
                  ? u.default
                      .getInstance()
                      .getMyselfUserInfo()
                      .setNickName(this.edit_name.string)
                  : l.default
                      .getInstance()
                      .getTools()
                      .showTips(d.default.replaceStr("userinfo_nickname"));
              }),
              (t.prototype.onBtnCloseClick = function () {
                l.default.getInstance().setIsOpenUser(!1), this.onClose();
              }),
              i([m(cc.Sprite)], t.prototype, "sprHeadPhoto", void 0),
              i([m(cc.Label)], t.prototype, "labNickName", void 0),
              i([m(cc.Sprite)], t.prototype, "sprCountry", void 0),
              i([m(cc.Label)], t.prototype, "label_country", void 0),
              i([m(cc.Label)], t.prototype, "labGold", void 0),
              i([m(cc.Label)], t.prototype, "labExp", void 0),
              i([m(cc.ProgressBar)], t.prototype, "progressExp", void 0),
              i(
                [m(cc.Prefab)],
                t.prototype,
                "modifyNickNameViewPrefab",
                void 0
              ),
              i(
                [m(cc.Prefab)],
                t.prototype,
                "modifyHeadPhotoViewPrefab",
                void 0
              ),
              i([m(cc.Prefab)], t.prototype, "modifyCountryViewPrefab", void 0),
              i([m(cc.Label)], t.prototype, "labWinRounds", void 0),
              i([m(cc.Node)], t.prototype, "base_node", void 0),
              i([m(cc.Node)], t.prototype, "img_bg", void 0),
              i([m(cc.EditBox)], t.prototype, "edit_name", void 0),
              i([m(cc.Label)], t.prototype, "label_exp", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Utils/Utils": "Utils",
        "./ModifyCountryView": "ModifyCountryView",
        "./ModifyHeadPhotoView": "ModifyHeadPhotoView",
      },
    ],
    Utils: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "5ea09QIeiFAX4+4odAe8ZBa", "Utils"),
          Object.defineProperty(n, "__esModule", { value: !0 });
        var o = e("../Enum/GameConst"),
          a = e("../Enum/GameEnum"),
          i = e("../Manager/GameDataManager"),
          r = e("../Manager/RoomInfoManager"),
          s = e("../Manager/ShopDataManager"),
          c = e("../Manager/UserInfoManager"),
          l = (function () {
            function e() {}
            return (
              (e.getRandomNum = function (e, t) {
                var n = t - e,
                  o = Math.random();
                return e + Math.round(o * n);
              }),
              (e.getActivityRandomNum = function (e, t) {
                var n = t - e,
                  o = Math.random();
                return e + Math.ceil(o * n * 100) / 100;
              }),
              (e.randomOneUserId = function () {
                for (var e = "", t = 0; t < 8; t++)
                  e += this.getRandomNum(1, 9) + "";
                return e;
              }),
              (e.getCurTimeStamp = function () {
                return Date.parse(new Date().toString());
              }),
              (e.getCountdown = function () {
                var e = new Date(this.getCurTimeStamp()),
                  t = 23 - e.getHours(),
                  n = 59 - e.getMinutes(),
                  o = 60 - e.getSeconds();
                return (
                  console.log(
                    "\u8ddd\u79bb\u665a\u4e0a12\u70b9\u8fd8\u6709" +
                      (3600 * t + 60 * n + o) +
                      "\u79d2"
                  ),
                  3600 * t + 60 * n + o
                );
              }),
              (e.countDown = function (e) {
                return "0:" + Math.floor(e / 60) + ":" + (e % 60);
              }),
              (e.getDurationSecond = function (t, n) {
                return (
                  n || (n = e.getCurTimeStamp()), Math.floor((n - t) / 1e3)
                );
              }),
              (e.genRandomDiamond = function () {
                var e = this.getRandomNum(1, 100);
                return e >= 1 && e <= 50 ? 50 : e > 50 && e <= 75 ? 100 : 150;
              }),
              (e.deepClone = function (e) {
                var t = Array.isArray(e) ? e : {};
                for (var n in e)
                  e.hasOwnProperty(n) &&
                    ("object" == typeof e[n] && null !== e[n]
                      ? (t[n] = this.deepClone(e[n]))
                      : (t[n] = e[n]));
                return t;
              }),
              (e.formatTime = function (e) {
                var t = Math.floor(e / 3600),
                  n = e % 3600,
                  o = Math.floor(n / 60),
                  a = n % 60;
                return (
                  (t < 10 ? "0" + t : "" + t) +
                  ":" +
                  (o < 10 ? "0" + o : "" + o) +
                  ":" +
                  (a < 10 ? "0" + a : "" + a)
                );
              }),
              (e.formatMoney = function (e) {
                return e >= 1e5 ? e / 1e5 + "K" : e >= 1e8 ? e / 1e8 + "M" : e;
              }),
              (e.shuffle = function (e, t) {
                void 0 === t && (t = !0);
                var n = null;
                n = t ? e : e.slice();
                for (var o = 0; o < n.length; o++) {
                  var a = this.getRandomNum(0, o),
                    i = n[o];
                  (n[o] = n[a]), (n[a] = i);
                }
                return n;
              }),
              (e.getRandomArrayElements = function (e, t) {
                for (
                  var n, o = e.slice(0), a = e.length, i = a - t, r = 0;
                  a-- > i;

                )
                  (n = o[(r = Math.floor((a + 1) * Math.random()))]),
                    (o[r] = o[a]),
                    (o[a] = n);
                return o.slice(i);
              }),
              (e.getDateInfo = function (e) {
                var t = {
                    year: 0,
                    month: 0,
                    day: 0,
                    hour: 0,
                    minute: 0,
                    second: 0,
                    millisecond: 0,
                  },
                  n = new Date();
                return (
                  e && (n = new Date(e)),
                  (t.year = n.getFullYear()),
                  (t.month = n.getMonth() + 1),
                  (t.day = n.getDate()),
                  (t.hour = n.getHours()),
                  (t.minute = n.getMinutes()),
                  (t.second = n.getSeconds()),
                  (t.millisecond = n.getMilliseconds()),
                  t
                );
              }),
              (e.getDateString = function (e) {
                var t = this.getDateInfo(e);
                return t.year + "-" + t.month + "-" + t.day;
              }),
              (e.getDiffDay = function (e, t) {
                console.log("strDate1: " + e);
                var n = e.split("-");
                console.log(
                  "str1: " +
                    n +
                    "str1[0]" +
                    n[0] +
                    "  parseInt(str1[0]): " +
                    parseInt(n[0])
                );
                var o = t.split("-"),
                  a = n[0] + "/" + parseInt(n[1]) + "/" + parseInt(n[2]);
                console.log("str11: " + a);
                var i = o[0] + "/" + o[1] + "/" + o[2];
                console.log("str2: " + i);
                var r = Date.parse(a);
                console.log("myDate_1: " + r);
                var s = Date.parse(i);
                console.log("myDate_2: " + s);
                var c = Math.abs(r - s);
                return Math.floor(c / 864e5);
              }),
              (e.getWorldPosition = function (e) {
                return e.parent.convertToWorldSpaceAR(e.position);
              }),
              (e.splitCountArray = function (e, t) {
                for (
                  var n = [], o = Math.ceil(e.length / t), a = 0, i = 0;
                  i < o;
                  i++
                ) {
                  var r = [];
                  n.push(r);
                  for (var s = a; s < a + t; s++) e[s] && r.push(e[s]);
                  a += t;
                }
                return n;
              }),
              (e.getUINeedScale = function () {
                var e = cc.view.getVisibleSize(),
                  t = cc.view.getDesignResolutionSize(),
                  n = e.width / t.width,
                  o = e.height / t.height;
                return !(Math.abs(n - o) < 0.01);
              }),
              (e.regAnimationFinishEvent = function (e, t) {
                var n;
                (n = function () {
                  e.off("finished", n), t();
                }),
                  e.on("finished", n);
              }),
              (e.savePointTwoNumber = function (e) {
                return Number(e.toFixed(2));
              }),
              (e.getDicePointsByProbability = function (t, n) {
                if (
                  (cc.log(
                    "getDicePointsByProbability---dicePoints:" +
                      t +
                      " probability:" +
                      n
                  ),
                  t >= 1 && t <= o.DICE_MAX_POINTS)
                ) {
                  n < 0 ? (n = 0) : n > 1 && (n = 1);
                  var a = [1, 2, 3, 4, 5, 6],
                    i = a.indexOf(t);
                  if (0 == n)
                    return a.splice(i, 1), a[e.getRandomNum(0, a.length - 1)];
                  if (1 == n) return t;
                  (n = this.savePointTwoNumber(n)),
                    a.unshift(a.splice(i, 1)[0]);
                  var r = (1 - n) / 5;
                  (r = this.savePointTwoNumber(r)), (n *= 100), (r *= 100);
                  for (var s = [], c = 0, l = 0; l < a.length; l++) {
                    var u = a[l],
                      d = void 0;
                    if (0 == l)
                      d = { startNum: 1, endNum: n, probability: n, points: u };
                    else if (l == a.length - 1)
                      d = {
                        startNum: (p = c + 1),
                        endNum: 100,
                        probability: 100 - p + 1,
                        points: u,
                      };
                    else {
                      var p;
                      d = {
                        startNum: (p = c + 1),
                        endNum: p + r - 1,
                        probability: r,
                        points: u,
                      };
                    }
                    (c = d.endNum), s.push(d);
                  }
                  var f = e.getRandomNum(1, 100);
                  for (l = 0; l < s.length; l++)
                    if (f >= (d = s[l]).startNum && f <= d.endNum)
                      return d.points;
                } else
                  cc.log(
                    "getDicePointsByProbability, points:" +
                      t +
                      " is error points"
                  );
              }),
              (e.assignProbability = function (e, t) {
                var n = [];
                if (0 == e.length) return n;
                var o = this.savePointTwoNumber(t / e.length);
                (t *= 100), (o *= 100);
                for (var a = 0; a < e.length; a++)
                  if (a != e.length - 1) n.push(o);
                  else {
                    var i = t - o * (e.length - 1);
                    n.push(i);
                  }
                return n;
              }),
              (e.getDicePointsByProbability2 = function (t, n) {
                cc.log(
                  "getDicePointsByProbabilityArray---array:" +
                    JSON.stringify(t) +
                    " probability:" +
                    n
                );
                for (
                  var a = [1, 2, 3, 4, 5, 6], i = t, r = [], s = 0;
                  s < a.length;
                  s++
                )
                  i.indexOf(a[s]) == o.ARRAY_ELE_NOT_EXIST && r.push(a[s]);
                var c = this.savePointTwoNumber(n),
                  l = this.savePointTwoNumber(1 - c),
                  u = this.assignProbability(i, c),
                  d = this.assignProbability(r, l),
                  p = u.concat(d),
                  f = i.concat(r),
                  h = [],
                  g = 0;
                for (s = 0; s < f.length; s++) {
                  var m = f[s],
                    _ = p[s],
                    y = void 0;
                  if (0 == s)
                    y = { startNum: 1, endNum: _, probability: _, points: m };
                  else if (s == a.length - 1)
                    y = {
                      startNum: (v = g + 1),
                      endNum: 100,
                      probability: _,
                      points: m,
                    };
                  else {
                    var v;
                    y = {
                      startNum: (v = g + 1),
                      endNum: v + _ - 1,
                      probability: _,
                      points: m,
                    };
                  }
                  (g = y.endNum), h.push(y);
                }
                var I = e.getRandomNum(1, 100);
                for (s = 0; s < h.length; s++)
                  if (I >= (y = h[s]).startNum && I <= y.endNum)
                    return y.points;
              }),
              (e.isEqualFloatNumber = function (e, t) {
                return Math.abs(e - t) < 0.001;
              }),
              (e.localStr = function (t) {
                var n = t.getComponent(cc.Label);
                n && (n.string = e.replaceStr(n.string));
                var o = t.getComponent(cc.RichText);
                o && (o.string = e.replaceStr(o.string));
                for (var a = 0, i = t.children; a < i.length; a++) {
                  var r = i[a];
                  e.localStr(r);
                }
              }),
              (e.replaceStr = function (e, t) {
                void 0 === t && (t = null);
                var n = e,
                  o = i.default.getInstance().getTools().getLanguageJson(),
                  r = null;
                for (var s in o.info)
                  if (
                    o.info[s].key == e ||
                    o.info[s].english == e ||
                    o.info[s].Arabic == e ||
                    o.info[s].Hindi == e ||
                    o.info[s].Urdu == e
                  ) {
                    r = o.info[s];
                    break;
                  }
                if (r)
                  switch (c.default.getInstance().getLanguage()) {
                    case a.LanguageType.English:
                      n = r.english.replace("##", t);
                      break;
                    case a.LanguageType.Arabic:
                      n = r.Arabic.replace("##", t);
                      break;
                    case a.LanguageType.Hindi:
                      n = r.Hindi.replace("##", t);
                      break;
                    case a.LanguageType.Urdu:
                      n = r.Urdu.replace("##", t);
                  }
                return n;
              }),
              (e.getLanguagePath = function () {
                return ["english_", "arabic_", "hindi_", "urdu_"][
                  c.default.getInstance().getLanguage() - 1
                ];
              }),
              (e.getEventName = function () {
                return r.default.getInstance().getGameMode() ==
                  a.GameMode.Online
                  ? r.default.getInstance().getRoomMode() ==
                    a.GameRoomMode.Quick
                    ? a.BuriedOneKey.onlineQuickGameRoom
                    : a.BuriedOneKey.onlineClassicGameRoom
                  : r.default.getInstance().getGameMode() == a.GameMode.Computer
                  ? r.default.getInstance().getComputerRoomMode() ==
                    a.GameRoomMode.Quick
                    ? a.BuriedOneKey.robotQuickGameRoom
                    : a.BuriedOneKey.robotClassicGameRoom
                  : a.BuriedOneKey.localGameRoom;
              }),
              (e.getUserName = function () {
                var t = [
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "h",
                    "i",
                    "j",
                    "k",
                    "l",
                    "m",
                    "n",
                    "o",
                    "p",
                    "q",
                    "r",
                    "s",
                    "t",
                    "u",
                    "v",
                    "w",
                    "x",
                    "y",
                    "z",
                  ],
                  n = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                  o = e.getRandomNum(1, 26),
                  a = e.getRandomNum(1, 26),
                  i = e.getRandomNum(1, 26),
                  r = e.getRandomNum(1, 10),
                  s = e.getRandomNum(1, 10),
                  c = e.getRandomNum(1, 10),
                  l = e.getRandomNum(1, 10),
                  u = e.getRandomNum(3, 10);
                return (
                  t[o - 1] +
                  t[a - 1] +
                  t[i - 1] +
                  "****" +
                  n[r - 1] +
                  n[s - 1] +
                  n[c - 1] +
                  n[l - 1] +
                  " exchanged the Call Credit through " +
                  u +
                  " days"
                );
              }),
              (e.getWeekDate = function () {
                return new Date(this.getCurTimeStamp()).getDay();
              }),
              (e.getDayToTimeStamp = function (e) {
                var t = Date.parse(e);
                return console.log("getDayToTimeStamp:" + t), t;
              }),
              (e.formatTime2 = function (e) {
                var t = e % 86400,
                  n = t % 3600;
                return (
                  Math.floor(e / 3600 / 24) +
                  "d " +
                  Math.floor(t / 3600) +
                  "h " +
                  Math.floor(n / 60) +
                  "m"
                );
              }),
              (e.getItemInfo = function (e) {
                var t = i.default.getInstance().getTools().getItem();
                for (var n in t.info) {
                  var o = t.info[n];
                  if (o.id == e) return o;
                }
                return null;
              }),
              (e.getDebrisID = function (t) {
                for (var n = [], o = [], i = 0; i < t.length; i++)
                  if (t[i]) {
                    var r = 0;
                    t[i].type == a.SkinType.Dice
                      ? (r = 6)
                      : t[i].type == a.SkinType.Token && (r = 4);
                    for (var c = 0; c < r; c++)
                      o.push(t[i].debrisID + c),
                        s.default
                          .getInstance()
                          .isHaveDebris(t[i].debrisID + c) ||
                          n.push(t[i].debrisID + c);
                  }
                return (
                  console.log("debrisList: " + n.length),
                  n.length > 0
                    ? e.getRandomArrayElements(n, 1)[0]
                    : e.getRandomArrayElements(o, 1)[0]
                );
              }),
              (e.getHours = function () {
                return new Date(this.getCurTimeStamp()).getHours();
              }),
              (e.countNum = function (e, t) {
                for (var n = 0, o = 0; o < e.length; o++) e[o] == t && n++;
                return n;
              }),
              e
            );
          })();
        (n.default = l), cc._RF.pop();
      },
      {
        "../Enum/GameConst": "GameConst",
        "../Enum/GameEnum": "GameEnum",
        "../Manager/GameDataManager": "GameDataManager",
        "../Manager/RoomInfoManager": "RoomInfoManager",
        "../Manager/ShopDataManager": "ShopDataManager",
        "../Manager/UserInfoManager": "UserInfoManager",
      },
    ],
    WatchADOutView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "c9022wkXRBGE5Syo6eDdQrd", "WatchADOutView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/BuriedPointManager"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/RoomInfoManager"),
          d = e("../Framework/Native/NativeBridge"),
          p = e("../Framework/Utils/Utils"),
          f = cc._decorator,
          h = f.ccclass,
          g = f.property,
          m = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.node_bg = null),
                (t._finishCallback = null),
                (t.btn_close = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                p.default.localStr(this.node),
                  l.default.getInstance().getTools().getGlobalJson();
              }),
              (t.prototype.onClickClose = function () {
                var e = this;
                c.default
                  .getInstance()
                  .sendBuriedPointInfo({
                    event: s.BuriedPointKey.WatchADOut,
                    isWatch: !1,
                  }),
                  l.default.getInstance().setWatchADOut(!1);
                var t = s.ADType.ShowComputerPlay;
                u.default.getInstance().getGameMode() == s.GameMode.Online &&
                  (t = s.ADType.ShowOnlinePlay),
                  d.default.watchVideo(function () {
                    e._finishCallback();
                  }, t);
              }),
              (t.prototype.setFinishCallback = function (e) {
                this._finishCallback = e;
              }),
              (t.prototype.onClickOkay = function () {
                var e = this;
                l.default.getInstance().getTools().showNoNetWorkTip() &&
                  (c.default
                    .getInstance()
                    .sendBuriedPointInfo({
                      event: s.BuriedPointKey.WatchADOut,
                      isWatch: !0,
                    }),
                  d.default.watchVideo(function () {
                    l.default.getInstance().setWatchADOut(!0),
                      e._finishCallback();
                  }, s.ADType.ChessOut));
              }),
              (t.prototype.hideBg = function () {
                this.node_bg.active = !1;
              }),
              i([g(cc.Node)], t.prototype, "node_bg", void 0),
              i([g(cc.Button)], t.prototype, "btn_close", void 0),
              i([h], t)
            );
          })(r.default);
        (n.default = m), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/BuriedPointManager": "BuriedPointManager",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    WebSock: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "70df2VbIU9B66Fr+op8FKJp", "WebSock"),
          Object.defineProperty(n, "__esModule", { value: !0 }),
          (n.WebSock = void 0);
        var o = (function () {
          function e() {
            (this._ws = null),
              (this.onConnected = null),
              (this.onMessage = null),
              (this.onError = null),
              (this.onClosed = null);
          }
          return (
            (e.prototype.connect = function (e) {
              var t = this;
              if (this._ws && this._ws.readyState === WebSocket.CONNECTING)
                return (
                  console.log("websocket connecting, wait for a moment..."), !1
                );
              var n = null;
              if (e.url) n = e.url;
              else {
                var o = e.ip,
                  a = e.port;
                n = e.protocol + "://" + o + ":" + a;
              }
              return (
                (this._ws = new WebSocket(n)),
                (this._ws.binaryType = e.binaryType
                  ? e.binaryType
                  : "arraybuffer"),
                (this._ws.onmessage = function (e) {
                  t.onMessage(e.data);
                }),
                (this._ws.onopen = this.onConnected),
                (this._ws.onerror = this.onError),
                (this._ws.onclose = this.onClosed),
                !0
              );
            }),
            (e.prototype.send = function (e) {
              return (
                this._ws.readyState == WebSocket.OPEN && (this._ws.send(e), !0)
              );
            }),
            (e.prototype.close = function (e, t) {
              this._ws.close(e, t);
            }),
            e
          );
        })();
        (n.WebSock = o), cc._RF.pop();
      },
      {},
    ],
    activityCell: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "953acJ8PvFNEpcpu3MBLXW3", "activityCell");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameEnum"),
          c = e("../../Framework/Manager/CirculateManager"),
          l = e("../../Framework/Manager/GameDataManager"),
          u = e("../../Framework/Manager/UserInfoManager"),
          d = e("../../Framework/Utils/Utils"),
          p = cc._decorator,
          f = p.ccclass,
          h = p.property,
          g = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_bg = null),
                (t.img_icon = null),
                (t.img_reward = null),
                (t.img_play = null),
                (t.label_win_count = null),
                (t.label_name = null),
                (t.node_time = null),
                (t.label_time = null),
                (t.img_btn = null),
                (t.label_start = null),
                (t.img_gold = null),
                (t.label_gold = null),
                (t.label_openTime = null),
                (t.activityData = null),
                (t.endTime = 0),
                (t.todayColor = cc.color(182, 98, 0)),
                (t.progressColor = cc.color(51, 0, 136)),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.initData = function (e) {
                (this.activityData = e), this.showUI();
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showUI = function () {
                var e = this;
                this.loadRes(
                  this.activityData.icon,
                  cc.SpriteFrame,
                  function (t) {
                    e.img_icon.spriteFrame = t;
                  }
                ),
                  this.loadRes(
                    this.activityData.rewardIcon,
                    cc.SpriteFrame,
                    function (t) {
                      e.img_reward.spriteFrame = t;
                    }
                  ),
                  (this.label_name.string = this.activityData.name);
                var t = c.default
                    .getInstance()
                    .getActivityState(this.activityData),
                  n = "";
                l.default
                  .getInstance()
                  .getTools()
                  .setNodeMaterial(this.img_btn, t != s.activityState.progress),
                  l.default
                    .getInstance()
                    .getTools()
                    .setNodeMaterial(
                      this.label_start,
                      t != s.activityState.progress
                    ),
                  l.default
                    .getInstance()
                    .getTools()
                    .setNodeMaterial(
                      this.img_gold,
                      t != s.activityState.progress
                    ),
                  l.default
                    .getInstance()
                    .getTools()
                    .setNodeMaterial(
                      this.label_gold,
                      t != s.activityState.progress
                    ),
                  t == s.activityState.today
                    ? ((n = "today"),
                      (this.node_time.active = !1),
                      (this.label_start.string = this.activityData.staryTitle),
                      (this.label_openTime.node.active = !0),
                      (this.label_openTime.string =
                        this.activityData.startTime + ":00"),
                      (this.img_gold.node.active = !1),
                      (this.label_gold.node.active = !1),
                      (this.label_name.node.getComponent(
                        cc.LabelOutline
                      ).color = this.todayColor))
                    : t == s.activityState.progress &&
                      ((n = "progress"),
                      (this.node_time.active = !0),
                      (this.label_start.string = "Start"),
                      (this.label_openTime.node.active = !1),
                      (this.img_gold.node.active = !0),
                      (this.label_gold.node.active = !0),
                      (this.label_gold.string = this.activityData.gold),
                      (this.label_name.node.getComponent(
                        cc.LabelOutline
                      ).color = this.progressColor),
                      (this.endTime = this.getEndTime()),
                      this.endTime > 0 &&
                        (this.updateTime(), this.schedule(this.updateTime, 1))),
                  (this.label_win_count.string =
                    c.default
                      .getInstance()
                      .getActivityCount(this.activityData.activityType) + ""),
                  this.loadRes("img_" + n, cc.SpriteFrame, function (t) {
                    e.img_bg.spriteFrame = t;
                  }),
                  this.loadRes(
                    "img_" + n + "_play",
                    cc.SpriteFrame,
                    function (t) {
                      e.img_play.spriteFrame = t;
                    }
                  );
              }),
              (t.prototype.onBtnStartClick = function () {
                c.default.getInstance().getActivityState(this.activityData) !=
                  s.activityState.today &&
                  (u.default.getInstance().getMyselfUserInfo().getGoldNum() >=
                  this.activityData.gold
                    ? ((c.default.getInstance().circulateActivity =
                        this.activityData.activityType),
                      this.activityData.activityType == s.circulateActivity.cup
                        ? (c.default.getInstance().gameMode =
                            s.GameMode.BombItem)
                        : (c.default.getInstance().gameMode =
                            s.GameMode.Roadblock),
                      cc.director.emit(
                        s.GameEvent.showActivityMatch,
                        this.activityData
                      ))
                    : l.default
                        .getInstance()
                        .getTools()
                        .showTips(
                          d.default.replaceStr("store_insufficientgoldcoins")
                        ));
              }),
              (t.prototype.updateTime = function () {
                this.endTime > 0
                  ? ((this.label_time.string = d.default.formatTime2(
                      this.endTime
                    )),
                    this.endTime--)
                  : (this.unschedule(this.updateTime), this.showUI());
              }),
              (t.prototype.getEndTime = function () {
                var e = 0,
                  t = d.default.getWeekDate(),
                  n = c.default
                    .getInstance()
                    .activityOpenDay(
                      this.activityData.startDay,
                      this.activityData.sustainTime,
                      this.activityData.startTime
                    );
                if (-1 != n.indexOf(t))
                  if (this.activityData.startDay == t) {
                    var o = d.default.getDateString(
                      d.default.getCurTimeStamp()
                    );
                    console.log("\u6d3b\u52a8\u8d77\u59cb\u65f6\u95f4: " + o);
                    var a =
                      d.default.getDayToTimeStamp(o) +
                      1e3 *
                        (3600 * this.activityData.startTime +
                          3600 * this.activityData.sustainTime -
                          28800);
                    console.log("endtime: " + a),
                      (e = (a - d.default.getCurTimeStamp()) / 1e3);
                  } else {
                    var i = new Date(d.default.getCurTimeStamp()),
                      r = i.getHours(),
                      s = 59 - i.getMinutes();
                    e =
                      3600 *
                        (this.activityData.sustainTime -
                          r -
                          (24 - this.activityData.startTime) -
                          1 -
                          24 * (n.indexOf(t) - 1)) +
                      60 * s;
                  }
                return console.log("\u5269\u4f59\u65f6\u95f4: " + e), e;
              }),
              (t.prototype.onBtnHelpClick = function () {
                cc.director.emit(
                  s.GameEvent.showActivityHelp,
                  this.activityData.activityType
                );
              }),
              i([h(cc.Sprite)], t.prototype, "img_bg", void 0),
              i([h(cc.Sprite)], t.prototype, "img_icon", void 0),
              i([h(cc.Sprite)], t.prototype, "img_reward", void 0),
              i([h(cc.Sprite)], t.prototype, "img_play", void 0),
              i([h(cc.Label)], t.prototype, "label_win_count", void 0),
              i([h(cc.Label)], t.prototype, "label_name", void 0),
              i([h(cc.Node)], t.prototype, "node_time", void 0),
              i([h(cc.Label)], t.prototype, "label_time", void 0),
              i([h(cc.Sprite)], t.prototype, "img_btn", void 0),
              i([h(cc.Label)], t.prototype, "label_start", void 0),
              i([h(cc.Sprite)], t.prototype, "img_gold", void 0),
              i([h(cc.Label)], t.prototype, "label_gold", void 0),
              i([h(cc.Label)], t.prototype, "label_openTime", void 0),
              i([f], t)
            );
          })(r.default);
        (n.default = g), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    activityHelp: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "7eb07JEtD9ETLJSnKHTzEKe", "activityHelp");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = cc._decorator,
          c = s.ccclass,
          l = s.property,
          u = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_point_list = []),
                (t.spr_point = []),
                (t.page = null),
                (t.index = 0),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.updateUI();
              }),
              (t.prototype.start = function () {}),
              (t.prototype.updateReward = function () {}),
              (t.prototype.updateUI = function () {
                for (var e = 0; e < this.img_point_list.length; e++)
                  this.img_point_list[e].spriteFrame =
                    this.index == e ? this.spr_point[0] : this.spr_point[1];
              }),
              (t.prototype.onBtnPointClick = function (e, t) {
                var n = parseInt(t);
                n != this.index &&
                  ((this.index = n),
                  this.page.scrollToPage(n, 0.5),
                  this.updateUI());
              }),
              (t.prototype.pageviewCallBack = function () {
                (this.index = this.page.getCurrentPageIndex()), this.updateUI();
              }),
              i([l(cc.Sprite)], t.prototype, "img_point_list", void 0),
              i([l(cc.SpriteFrame)], t.prototype, "spr_point", void 0),
              i([l(cc.PageView)], t.prototype, "page", void 0),
              i([c], t)
            );
          })(r.default);
        (n.default = u), cc._RF.pop();
      },
      { "../../Framework/Base/BaseComponent": "BaseComponent" },
    ],
    activityMatchPlayerView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "385c0xy5E9DCpUjJTzkYVI4", "activityMatchPlayerView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameConst"),
          c = e("../../Framework/Enum/GameEnum"),
          l = e("../../Framework/Manager/AudioManager"),
          u = e("../../Framework/Manager/CirculateManager"),
          d = e("../../Framework/Manager/GameDataManager"),
          p = e("../../Framework/Manager/RoomInfoManager"),
          f = e("../../Framework/Manager/UserInfoManager"),
          h = e("../../Framework/Utils/Utils"),
          g = e("../TurnHeadPhotoAnim"),
          m = cc._decorator,
          _ = m.ccclass,
          y = m.property,
          v = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_title = null),
                (t.sprMyHeadPhoto = null),
                (t.labMyNickName = null),
                (t.nodePlayers = []),
                (t.label_name = []),
                (t.activityData = null),
                (t.isStartMatch = !1),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.initData = function (e) {
                h.default.localStr(this.node),
                  (this.activityData = e),
                  this.showUI();
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showUI = function () {
                var e = this;
                this.setMyHeadPhoto(),
                  this.setMyNickName(),
                  this.loadRes(
                    this.activityData.titleIcon,
                    cc.SpriteFrame,
                    function (t) {
                      e.img_title.spriteFrame = t;
                    }
                  );
              }),
              (t.prototype.setMyHeadPhoto = function () {
                var e = this,
                  t = f.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getHeadPhotoIdx();
                this.loadRes(
                  s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + t,
                  cc.SpriteFrame,
                  function (t) {
                    e.sprMyHeadPhoto.spriteFrame = t;
                  }
                );
              }),
              (t.prototype.setMyNickName = function () {
                this.labMyNickName.string = f.default
                  .getInstance()
                  .getMyselfUserInfo()
                  .getNickName();
              }),
              (t.prototype.onBtnCloseClick = function () {
                this.isStartMatch ||
                  (cc.director.emit(c.GameEvent.closeActivity), this.onClose());
              }),
              (t.prototype.onBtnBackClick = function () {
                this.isStartMatch || this.onClose();
              }),
              (t.prototype.onBtnHelpClick = function () {
                this.isStartMatch ||
                  cc.director.emit(
                    c.GameEvent.showActivityHelp,
                    this.activityData.activityType
                  );
              }),
              (t.prototype.onBtnPlayClick = function () {
                var e = f.default.getInstance().getMyselfUserInfo(),
                  t = e.getGoldNum();
                if (t >= this.activityData.gold) {
                  if (
                    (e.setGoldNum(t - this.activityData.gold),
                    !this.isStartMatch)
                  ) {
                    for (var n = 0; n < this.label_name.length; n++)
                      this.label_name[n].node.active = !1;
                    this.matchOtherPlayers(), (this.isStartMatch = !0);
                  }
                } else
                  d.default
                    .getInstance()
                    .getTools()
                    .showTips(
                      h.default.replaceStr("store_insufficientgoldcoins")
                    );
              }),
              (t.prototype.matchOtherPlayers = function () {
                var e = this;
                p.default.getInstance().setPlayerCount(4),
                  f.default.getInstance().generateGameUser();
                var t = f.default.getInstance().getOhterUser(),
                  n = p.default.getInstance().getPlayerCount();
                (u.default.getInstance().rankIndex = 16),
                  (u.default.getInstance().lostCount = 0),
                  (u.default.getInstance().competitionList = []),
                  (u.default.getInstance().competitionCount = 0),
                  (u.default.getInstance().isActivitying = !0),
                  (d.default.getInstance().bomb = {});
                for (
                  var o = 0,
                    a = function (a) {
                      i.loadRes(
                        s.HALL_PREFAB_PATH + "TurnHeadPhotoAnim",
                        cc.Prefab,
                        function (i) {
                          var r = null,
                            s = cc.instantiate(i),
                            l = s.getComponent(g.default);
                          n == c.PlayerCount.Two
                            ? ((s.parent = e.nodePlayers[1]),
                              (r =
                                e.nodePlayers[1].getChildByName("nodeSaoMiao")))
                            : ((s.parent = e.nodePlayers[a]),
                              (r =
                                e.nodePlayers[a].getChildByName(
                                  "nodeSaoMiao"
                                ))),
                            (r.zIndex = 10),
                            l.setInfo(
                              t[a].getNickName(),
                              t[a].getHeadPhotoIdx()
                            ),
                            l.startTurn(function () {
                              (r.active = !1),
                                (o += 1) == t.length && e.matchOver();
                            });
                        }
                      );
                    },
                    i = this,
                    r = 0;
                  r < t.length;
                  r++
                )
                  a(r);
              }),
              (t.prototype.matchOver = function () {
                (u.default.getInstance().isGameover = !1),
                  p.default
                    .getInstance()
                    .setGameMode(u.default.getInstance().gameMode),
                  p.default.getInstance().setRoomMode(c.GameRoomMode.Quick),
                  d.default.getInstance().setFristEnterGame(!1),
                  p.default.getInstance().setEntryGold(0),
                  p.default
                    .getInstance()
                    .setComputerChessColor(c.ChessColor.Blue),
                  this.scheduleOnce(function () {
                    l.default.getInstance().stopAllAudio(),
                      cc.director.loadScene("Game_grass");
                  }, 0.01);
              }),
              i([y(cc.Sprite)], t.prototype, "img_title", void 0),
              i([y(cc.Sprite)], t.prototype, "sprMyHeadPhoto", void 0),
              i([y(cc.Label)], t.prototype, "labMyNickName", void 0),
              i([y(cc.Node)], t.prototype, "nodePlayers", void 0),
              i([y(cc.Label)], t.prototype, "label_name", void 0),
              i([_], t)
            );
          })(r.default);
        (n.default = v), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameConst": "GameConst",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/AudioManager": "AudioManager",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../../Framework/Utils/Utils": "Utils",
        "../TurnHeadPhotoAnim": "TurnHeadPhotoAnim",
      },
    ],
    activityView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "fd7c6Y+3EtJs7i+xDBX/Lhd", "activityView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameEnum"),
          c = e("../../Framework/Manager/CirculateManager"),
          l = e("./activityCell"),
          u = cc._decorator,
          d = u.ccclass,
          p = u.property,
          f = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.layout_content = null),
                (t.pre_activity = null),
                (t.activityList = []),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.registerAllEvents(),
                  (this.activityList = c.default
                    .getInstance()
                    .getActivityList()),
                  this.showUi();
              }),
              (t.prototype.registerAllEvents = function () {
                this.registerEvent(
                  s.GameEvent.closeActivity,
                  this.onClose,
                  this
                );
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showUi = function () {
                for (var e = 0; e < this.activityList.length; e++)
                  if (this.activityList[e]) {
                    var t = cc.instantiate(this.pre_activity);
                    (t.parent = this.layout_content),
                      t.getComponent(l.default).initData(this.activityList[e]);
                  }
              }),
              (t.prototype.onBtnCloseClick = function () {
                this.onClose();
              }),
              i([p(cc.Node)], t.prototype, "layout_content", void 0),
              i([p(cc.Prefab)], t.prototype, "pre_activity", void 0),
              i([d], t)
            );
          })(r.default);
        (n.default = f), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "./activityCell": "activityCell",
      },
    ],
    addGuideView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "404f4Y4AohFkbvnPnnPFcDI", "addGuideView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/GameDataManager"),
          l = e("../Framework/Manager/UserInfoManager"),
          u = e("../Framework/Native/NativeBridge"),
          d = cc._decorator,
          p = d.ccclass,
          f = d.property,
          h = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.node_done = null),
                (t.node_btnGo = null),
                (t.node_btnGet = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                this.showUI();
              }),
              (t.prototype.showUI = function () {
                var e = c.default.getInstance().getIsCompleteGuide();
                (this.node_btnGo.active = !e),
                  (this.node_btnGet.active = e),
                  (this.node_done.active = e);
              }),
              (t.prototype.onBtnGoClick = function () {
                var e = this;
                u.default.addToHomeScreen(function () {
                  c.default.getInstance().setIsCompleteGuide(!0), e.showUI();
                });
              }),
              (t.prototype.onBtnGetClick = function () {
                var e = this,
                  t = l.default.getInstance().getMyselfUserInfo();
                c.default
                  .getInstance()
                  .getTools()
                  .playFlyEffect(
                    s.FlyEffectType.Coins,
                    cc.v3(0, 0, 0),
                    2e3,
                    function () {
                      t.setGoldNum(t.getGoldNum() + 2e3),
                        c.default.getInstance().setIsGetAppletReward(!0),
                        cc.director.emit(s.GameEvent.Update_Applet_Icon),
                        e.onClose();
                    }
                  );
              }),
              i([f(cc.Node)], t.prototype, "node_done", void 0),
              i([f(cc.Node)], t.prototype, "node_btnGo", void 0),
              i([f(cc.Node)], t.prototype, "node_btnGet", void 0),
              i([p], t)
            );
          })(r.default);
        (n.default = h), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
      },
    ],
    bombResult: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "0e92aSNsAJK97sgXsc4INHA", "bombResult");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameConst"),
          c = e("../../Framework/Enum/GameEnum"),
          l = e("../../Framework/Manager/CirculateManager"),
          u = e("../../Framework/Manager/GameDataManager"),
          d = e("../../Framework/Manager/ShopDataManager"),
          p = e("../../Framework/Manager/UserInfoManager"),
          f = e("./boxRewardCell"),
          h = cc._decorator,
          g = h.ccclass,
          m = h.property,
          _ = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_win_bg = null),
                (t.img_win = null),
                (t.node_layout_reward = null),
                (t.pre_reward = null),
                (t.label_text = null),
                (t.node_win = null),
                (t.label_rank = null),
                (t.isWin = !1),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                l.default.getInstance().isPlayAgain = !1;
              }),
              (t.prototype.initData = function () {
                var e = this,
                  t = l.default.getInstance().rankIndex;
                (this.isWin = t < 9),
                  (this.label_rank.string = t + ""),
                  (this.label_rank.node.color = this.isWin
                    ? cc.color(255, 216, 0)
                    : cc.color(186, 186, 186)),
                  (this.label_rank.node.getComponent(cc.LabelOutline).color =
                    this.isWin ? s.BROWN : s.GREY2),
                  (this.node_win.active = this.isWin),
                  (l.default.getInstance().isActivitying = !1);
                var n = this.isWin ? "img_cup_win_bg" : "img_cup_lost_bg",
                  o = this.isWin ? "img_cup_win" : "img_cup_lost";
                this.loadRes(n, cc.SpriteFrame, function (t) {
                  e.img_win_bg.spriteFrame = t;
                }),
                  this.loadRes(o, cc.SpriteFrame, function (t) {
                    e.img_win.spriteFrame = t;
                  }),
                  (this.isWin || l.default.getInstance().rankIndex < 9) &&
                    (this.showReward(),
                    l.default
                      .getInstance()
                      .addActivityCount(
                        l.default.getInstance().circulateActivity
                      )),
                  (this.label_text.string =
                    1 == t
                      ? "You did\uff01Great game\uff01"
                      : t > 1 && t < 9
                      ? "Reap the rewards and keep up the hard work\uff01"
                      : "Try again. You might win next time\uff01");
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showReward = function () {
                var e,
                  t = u.default.getInstance().getTools().getCupReward(),
                  n = [],
                  o = [],
                  a = l.default.getInstance().rankIndex;
                for (var i in ((e =
                  5 == a || 6 == a ? 5 : 7 == a || 8 == a ? 6 : a),
                t.info))
                  if (t.info[i].id == e) {
                    n = t.info[i].reward.split(",");
                    break;
                  }
                var r = p.default.getInstance().getMyselfUserInfo(),
                  s =
                    (d.default.getInstance().getDebrisIDList(118),
                    function (e) {
                      var t = { rewardType: 0, id: 0 };
                      n[2 * e] == c.Item.Gold &&
                        ((t.rewardType = c.Item.Gold),
                        (t.id = n[2 * e + 1]),
                        o.push(t),
                        u.default
                          .getInstance()
                          .getTools()
                          .playFlyEffect(
                            c.FlyEffectType.Coins,
                            null,
                            null,
                            function () {
                              r.setGoldNum(
                                r.getGoldNum() + parseInt(n[2 * e + 1])
                              );
                            }
                          ));
                    });
                for (i = 0; i < n.length / 2; i++) s(i);
                for (i = 0; i < o.length; i++) {
                  var h = cc.instantiate(this.pre_reward);
                  (h.parent = this.node_layout_reward),
                    h.getComponent(f.default).showUI(o[i]);
                }
              }),
              (t.prototype.onBtnBackClick = function () {
                (l.default.getInstance().isPlayAgain = !0),
                  cc.director.loadScene("Hall");
              }),
              (t.prototype.onBtnPlayAgainClick = function () {
                (l.default.getInstance().isPlayMatch = !0),
                  cc.director.loadScene("Hall");
              }),
              i([m(cc.Sprite)], t.prototype, "img_win_bg", void 0),
              i([m(cc.Sprite)], t.prototype, "img_win", void 0),
              i([m(cc.Node)], t.prototype, "node_layout_reward", void 0),
              i([m(cc.Prefab)], t.prototype, "pre_reward", void 0),
              i([m(cc.Label)], t.prototype, "label_text", void 0),
              i([m(cc.Node)], t.prototype, "node_win", void 0),
              i([m(cc.Label)], t.prototype, "label_rank", void 0),
              i([g], t)
            );
          })(r.default);
        (n.default = _), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameConst": "GameConst",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/ShopDataManager": "ShopDataManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "./boxRewardCell": "boxRewardCell",
      },
    ],
    boxRewardCell: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "a3afdkA2nhOZJquoLJfLJ7f", "boxRewardCell");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameEnum"),
          c = e("../../Framework/Manager/ShopDataManager"),
          l = e("../../Framework/Utils/Utils"),
          u = cc._decorator,
          d = u.ccclass,
          p = u.property,
          f = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_icon = null),
                (t.label_count = null),
                (t.node_debris = null),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.start = function () {}),
              (t.prototype.showUI = function (e) {
                var t = this;
                this.img_icon.node.scale = 1;
                var n = "";
                switch (
                  ((this.label_count.string = "x1"), parseInt(e.rewardType))
                ) {
                  case s.Item.Gold:
                    (n = "gold"), (this.label_count.string = "x" + e.id);
                    break;
                  case s.Item.Diamond:
                    (n = "dia"), (this.label_count.string = "x" + e.id);
                    break;
                  case s.Item.Bomb:
                    n = "bomb";
                    break;
                  case s.Item.Shield:
                    (n = "img_shield"), (this.img_icon.node.scale = 0.7);
                    break;
                  case s.Item.Medal:
                    this.img_icon.node.scale = 0.3;
                    break;
                  case s.Item.SkinDebris:
                  case s.Item.DiceDebris:
                  case s.Item.TokenDebris:
                    this.node_debris.active = !0;
                    var o = l.default.getItemInfo(e.id);
                    (n = o.icon),
                      o.type == s.SkinType.Dice
                        ? (this.img_icon.node.scale = 0.5)
                        : (this.img_icon.node.scale = 1);
                    break;
                  case s.Item.MaxReward:
                    n = "img_victory";
                    break;
                  case s.Item.ShopSkin:
                  case s.Item.HeadFrame:
                  case s.Item.Head:
                    (n = c.default.getInstance().getSkinInfo(e.id).icon),
                      (this.img_icon.node.scale = 0.5);
                }
                this.loadRes(n, cc.SpriteFrame, function (e) {
                  t.img_icon.spriteFrame = e;
                }),
                  (307 != e.id && s.Item.TokenDebris != e.rewardType) ||
                    (this.img_icon.node.scale = 0.1);
              }),
              (t.prototype.setLabelColor = function (e) {
                (this.label_count.node.color = e),
                  (this.label_count.node.getComponent(cc.LabelOutline).enabled =
                    !1);
              }),
              i([p(cc.Sprite)], t.prototype, "img_icon", void 0),
              i([p(cc.Label)], t.prototype, "label_count", void 0),
              i([p(cc.Node)], t.prototype, "node_debris", void 0),
              i([d], t)
            );
          })(r.default);
        (n.default = f), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/ShopDataManager": "ShopDataManager",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    computerPlayCountView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "3d579bU8spG1IJLIyf6FBp5", "computerPlayCountView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/RoomInfoManager"),
          u = e("../Framework/Manager/UserInfoManager"),
          d = e("./WatchADOutView"),
          p = cc._decorator,
          f = p.ccclass,
          h =
            (p.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onBtnPlayerCountClick = function (e, t) {
                  var n = this,
                    o = parseInt(t);
                  l.default.getInstance().setComputerPlayerCount(o),
                    l.default.getInstance().setEntryGold(0),
                    l.default.getInstance().caculatePlayerWinGold(),
                    l.default
                      .getInstance()
                      .setComputerChessColor(c.ChessColor.Blue),
                    l.default.getInstance().setPlayerCount(o),
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "WatchADOutView",
                      cc.Prefab,
                      function (e) {
                        var t = cc.instantiate(e);
                        t.parent = n.node;
                        var o = t.getComponent(d.default);
                        o.hideBg(),
                          o.setFinishCallback(function () {
                            n.playGame();
                          });
                      }
                    );
                }),
                (t.prototype.playGame = function () {
                  l.default.getInstance().getGameMode() == c.GameMode.Computer
                    ? this.matchOtherPlayers()
                    : cc.director.emit(c.GameEvent.Popup_Match_Player);
                }),
                (t.prototype.matchOtherPlayers = function () {
                  var e = this;
                  u.default.getInstance().generateGameUser(),
                    u.default.getInstance().deductEntryGold(),
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "TransitionView",
                      cc.Prefab,
                      function (t) {
                        cc.instantiate(t).parent = e.node;
                      }
                    );
                }),
                (t.prototype.onBtnCloseClick = function () {
                  this.onClose();
                }),
                i([f], t)
              );
            })(r.default));
        (n.default = h), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "./WatchADOutView": "WatchADOutView",
      },
    ],
    computerRoomView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "10f02NQn21Jf4gn/UaALr4U", "computerRoomView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/RoomInfoManager"),
          u = e("../Framework/Utils/Utils"),
          d = cc._decorator,
          p = d.ccclass,
          f =
            (d.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  u.default.localStr(this.node);
                }),
                (t.prototype.onBtnGameModeClick = function (e, t) {
                  var n = this,
                    o =
                      parseInt(t) == c.GameRoomMode.Quick
                        ? c.GameRoomMode.Quick
                        : c.GameRoomMode.Classic;
                  l.default.getInstance().setComputerRoomMode(o),
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "computerPlayCountView",
                      cc.Prefab,
                      function (e) {
                        cc.instantiate(e).parent = n.node;
                      }
                    );
                }),
                (t.prototype.onBtnCloseClick = function () {
                  cc.director.emit(c.GameEvent.Close_Parent_Ui), this.onClose();
                }),
                i([p], t)
              );
            })(r.default));
        (n.default = f), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Utils/Utils": "Utils",
      },
    ],
    cupPoster: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "9eb822SKeBMSppdjBo9bz7A", "cupPoster");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameEnum"),
          c = e("../../Framework/Manager/CirculateManager"),
          l = e("../../Framework/Utils/Utils"),
          u = cc._decorator,
          d = u.ccclass,
          p =
            (u.property,
            (function (e) {
              function t() {
                var t = (null !== e && e.apply(this, arguments)) || this;
                return (t.activityData = null), t;
              }
              return (
                a(t, e),
                (t.prototype.onLoad = function () {
                  this.activityData = c.default
                    .getInstance()
                    .getActivityData(1);
                }),
                (t.prototype.start = function () {}),
                (t.prototype.onBtnStartClick = function () {
                  cc.director.emit(s.GameEvent.showActivityCup), this.onClose();
                }),
                (t.prototype.getEndTime = function () {
                  var e = 0,
                    t = l.default.getWeekDate(),
                    n = c.default
                      .getInstance()
                      .activityOpenDay(
                        this.activityData.startDay,
                        this.activityData.sustainTime,
                        this.activityData.startTime
                      );
                  if (-1 != n.indexOf(t))
                    if (this.activityData.startDay == t) {
                      var o = l.default.getDateString(
                        l.default.getCurTimeStamp()
                      );
                      console.log("\u6d3b\u52a8\u8d77\u59cb\u65f6\u95f4: " + o);
                      var a =
                        l.default.getDayToTimeStamp(o) +
                        1e3 *
                          (3600 * this.activityData.startTime +
                            3600 * this.activityData.sustainTime -
                            28800);
                      console.log("endtime: " + a),
                        (e = (a - l.default.getCurTimeStamp()) / 1e3);
                    } else {
                      var i = new Date(l.default.getCurTimeStamp()),
                        r = i.getHours(),
                        s = 59 - i.getMinutes();
                      e =
                        3600 *
                          (this.activityData.sustainTime -
                            r -
                            (24 - this.activityData.startTime) -
                            1 -
                            24 * (n.indexOf(t) - 1)) +
                        60 * s;
                    }
                  return console.log("\u5269\u4f59\u65f6\u95f4: " + e), e;
                }),
                i([d], t)
              );
            })(r.default));
        (n.default = p), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "../../Framework/Utils/Utils": "Utils",
      },
    ],
    expressionView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "3b61f5eLBxHYrTH2YT36v4D", "expressionView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = cc._decorator,
          l = c.ccclass,
          u =
            (c.property,
            (function (e) {
              function t() {
                var t = (null !== e && e.apply(this, arguments)) || this;
                return (t._playerIndex = 0), t;
              }
              return (
                a(t, e),
                (t.prototype.setPlayerIndex = function (e) {
                  this._playerIndex = e;
                }),
                (t.prototype.delectExpression = function () {
                  cc.director.emit(
                    s.GameEvent.delect_Expression,
                    this._playerIndex
                  );
                }),
                i([l], t)
              );
            })(r.default));
        (n.default = u), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
      },
    ],
    newPlayReward: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "9f7a6mrQmhLhoWRQftCLgF8", "newPlayReward");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameEnum"),
          c = e("../Framework/Manager/GameDataManager"),
          l = e("../Framework/Manager/UserInfoManager"),
          u = e("../Framework/Native/NativeBridge"),
          d = cc._decorator,
          p = d.ccclass,
          f =
            (d.property,
            (function (e) {
              function t() {
                return (null !== e && e.apply(this, arguments)) || this;
              }
              return (
                a(t, e),
                (t.prototype.onBtnGetReward = function () {
                  var e = this;
                  u.default.watchVideo(function () {
                    var t = l.default.getInstance().getMyselfUserInfo(),
                      n = c.default.getInstance().getHallDiamondPos();
                    c.default
                      .getInstance()
                      .getTools()
                      .playFlyEffect(
                        s.FlyEffectType.Diamonds,
                        n,
                        20,
                        function () {
                          t.setDiamondNum(t.getDiamondNum() + 20);
                        }
                      );
                    var o = c.default.getInstance().getHallGoldPos();
                    c.default
                      .getInstance()
                      .getTools()
                      .playFlyEffect(
                        s.FlyEffectType.Coins,
                        o,
                        3e3,
                        function () {
                          t.setGoldNum(t.getGoldNum() + 3e3);
                        }
                      ),
                      e.onClose();
                  }, s.ADType.NewPlayReward);
                }),
                (t.prototype.onBtnCloseUI = function () {
                  var e = l.default.getInstance().getMyselfUserInfo(),
                    t = c.default.getInstance().getHallDiamondPos();
                  c.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(
                      s.FlyEffectType.Diamonds,
                      t,
                      10,
                      function () {
                        e.setDiamondNum(e.getDiamondNum() + 10);
                      }
                    );
                  var n = c.default.getInstance().getHallGoldPos();
                  c.default
                    .getInstance()
                    .getTools()
                    .playFlyEffect(s.FlyEffectType.Coins, n, 1500, function () {
                      e.setGoldNum(e.getGoldNum() + 1500);
                    }),
                    cc.director.emit(s.GameEvent.Open_ActivityMain),
                    this.onClose();
                }),
                i([p], t)
              );
            })(r.default));
        (n.default = f), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
      },
    ],
    newRoomInfoView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "f19baUS06VHKI3skq2vy6yu", "newRoomInfoView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../Framework/Base/BaseComponent"),
          s = e("../Framework/Enum/GameConst"),
          c = e("../Framework/Enum/GameEnum"),
          l = e("../Framework/Manager/GameDataManager"),
          u = e("../Framework/Manager/RoomInfoManager"),
          d = e("../Framework/Manager/UserInfoManager"),
          p = e("../Framework/Native/NativeBridge"),
          f = e("../Framework/Utils/Utils"),
          h = e("./WatchADOutView"),
          g = cc._decorator,
          m = g.ccclass,
          _ = g.property,
          y = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.img_twe_bg = null),
                (t.img_twe = null),
                (t.img_four_bg = null),
                (t.img_four = null),
                (t.node_quick_mask = null),
                (t.node_classic_mask = null),
                (t.scroll_item = null),
                (t.list_item = []),
                (t.playCount = 4),
                (t.gameRoomMode = 0),
                (t.goldList = [500, 1e3, 5e3, 1e4, 5e4, 1e5]),
                (t.prizeGoldList = [950, 1900, 9500, 19e3, 95e3, 19e4]),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                f.default.localStr(this.node),
                  u.default.getInstance().getGameMode() == c.GameMode.Computer
                    ? ((this.playCount = u.default
                        .getInstance()
                        .getComputerPlayerCount()),
                      (this.gameRoomMode = u.default
                        .getInstance()
                        .getComputerRoomMode()))
                    : ((this.playCount = u.default
                        .getInstance()
                        .getOnlinePlayerCount()),
                      (this.gameRoomMode = u.default
                        .getInstance()
                        .getRoomMode())),
                  l.default.getInstance().getIsAgain() &&
                    (u.default.getInstance().getGameMode() == c.GameMode.Online
                      ? cc.director.emit(c.GameEvent.Popup_Match_Player)
                      : this.matchOtherPlayers(),
                    l.default.getInstance().setIsAgain(!1)),
                  this.updatePlayCount(),
                  this.updateGameRoomMode(),
                  this.updateItem();
              }),
              (t.prototype.updatePlayCount = function () {
                var e = this;
                2 == this.playCount
                  ? (this.loadRes(
                      "img_select_bg",
                      cc.SpriteFrame,
                      function (t) {
                        e.img_twe_bg.spriteFrame = t;
                      }
                    ),
                    this.loadRes(
                      "img_twe_select",
                      cc.SpriteFrame,
                      function (t) {
                        e.img_twe.spriteFrame = t;
                      }
                    ),
                    this.loadRes("img_bg", cc.SpriteFrame, function (t) {
                      e.img_four_bg.spriteFrame = t;
                    }),
                    this.loadRes("img_four", cc.SpriteFrame, function (t) {
                      e.img_four.spriteFrame = t;
                    }))
                  : (this.loadRes("img_bg", cc.SpriteFrame, function (t) {
                      e.img_twe_bg.spriteFrame = t;
                    }),
                    this.loadRes("img_twe", cc.SpriteFrame, function (t) {
                      e.img_twe.spriteFrame = t;
                    }),
                    this.loadRes("img_select_bg", cc.SpriteFrame, function (t) {
                      e.img_four_bg.spriteFrame = t;
                    }),
                    this.loadRes(
                      "img_four_select",
                      cc.SpriteFrame,
                      function (t) {
                        e.img_four.spriteFrame = t;
                      }
                    ));
              }),
              (t.prototype.updateGameRoomMode = function () {
                this.gameRoomMode == c.GameRoomMode.Quick
                  ? ((this.node_classic_mask.active = !0),
                    (this.node_quick_mask.active = !1))
                  : ((this.node_classic_mask.active = !1),
                    (this.node_quick_mask.active = !0));
              }),
              (t.prototype.updateItem = function () {
                for (var e = 0; e < this.list_item.length; e++) {
                  var t = this.list_item[e]
                      .getChildByName("label_money")
                      .getComponent(cc.Label),
                    n =
                      2 == this.playCount
                        ? this.prizeGoldList[e]
                        : 2 * this.prizeGoldList[e];
                  t.string = n + "";
                }
              }),
              (t.prototype.onBtnPlayCountClick = function (e, t) {
                (this.playCount = 1 == t ? 2 : 4),
                  u.default.getInstance().getGameMode() == c.GameMode.Online
                    ? u.default
                        .getInstance()
                        .setOnlinePlayerCount(this.playCount)
                    : u.default
                        .getInstance()
                        .setComputerPlayerCount(this.playCount),
                  u.default.getInstance().setPlayerCount(this.playCount),
                  this.updatePlayCount(),
                  this.updateItem();
              }),
              (t.prototype.onBtnGameRoomModeClick = function (e, t) {
                (this.gameRoomMode =
                  1 == t ? c.GameRoomMode.Quick : c.GameRoomMode.Classic),
                  u.default.getInstance().getGameMode() == c.GameMode.Online
                    ? u.default.getInstance().setRoomMode(this.gameRoomMode)
                    : u.default
                        .getInstance()
                        .setComputerRoomMode(this.gameRoomMode),
                  this.updateGameRoomMode();
              }),
              (t.prototype.onBtnCloseClick = function () {
                var e = this;
                p.default.watchVideo(function () {
                  cc.director.emit(c.GameEvent.Close_Parent_Ui), e.onClose();
                }, "onlineClose_Insert");
              }),
              (t.prototype.onBtnSelectItem = function (e, t) {
                var n = this,
                  o = this.goldList[parseInt(t)];
                d.default.getInstance().getMyselfUserInfo().getGoldNum() < o
                  ? l.default
                      .getInstance()
                      .getTools()
                      .showTips(
                        f.default.replaceStr("store_insufficientgoldcoins")
                      )
                  : (u.default.getInstance().setEntryGold(o),
                    u.default.getInstance().caculatePlayerWinGold(),
                    u.default
                      .getInstance()
                      .setComputerChessColor(c.ChessColor.Blue),
                    u.default
                      .getInstance()
                      .setOnlineChessColor(c.ChessColor.Blue),
                    this.loadRes(
                      s.HALL_PREFAB_PATH + "WatchADOutView",
                      cc.Prefab,
                      function (e) {
                        var t = cc.instantiate(e);
                        (t.parent = n.node),
                          t
                            .getComponent(h.default)
                            .setFinishCallback(function () {
                              n.playGame();
                            });
                      }
                    ));
              }),
              (t.prototype.playGame = function () {
                u.default.getInstance().getGameMode() == c.GameMode.Computer
                  ? this.matchOtherPlayers()
                  : (cc.director.emit(c.GameEvent.Popup_Match_Player),
                    this.onClose());
              }),
              (t.prototype.matchOtherPlayers = function () {
                var e = this;
                d.default.getInstance().generateGameUser(),
                  d.default.getInstance().deductEntryGold(),
                  this.loadRes(
                    s.HALL_PREFAB_PATH + "TransitionView",
                    cc.Prefab,
                    function (t) {
                      cc.instantiate(t).parent = e.node;
                    }
                  );
              }),
              i([_(cc.Sprite)], t.prototype, "img_twe_bg", void 0),
              i([_(cc.Sprite)], t.prototype, "img_twe", void 0),
              i([_(cc.Sprite)], t.prototype, "img_four_bg", void 0),
              i([_(cc.Sprite)], t.prototype, "img_four", void 0),
              i([_(cc.Node)], t.prototype, "node_quick_mask", void 0),
              i([_(cc.Node)], t.prototype, "node_classic_mask", void 0),
              i([_(cc.ScrollView)], t.prototype, "scroll_item", void 0),
              i([_(cc.Node)], t.prototype, "list_item", void 0),
              i([m], t)
            );
          })(r.default);
        (n.default = y), cc._RF.pop();
      },
      {
        "../Framework/Base/BaseComponent": "BaseComponent",
        "../Framework/Enum/GameConst": "GameConst",
        "../Framework/Enum/GameEnum": "GameEnum",
        "../Framework/Manager/GameDataManager": "GameDataManager",
        "../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../Framework/Native/NativeBridge": "NativeBridge",
        "../Framework/Utils/Utils": "Utils",
        "./WatchADOutView": "WatchADOutView",
      },
    ],
    promotionView: [
      function (e, t, n) {
        "use strict";
        cc._RF.push(t, "36d0db788pIdo6vkwHrdBsO", "promotionView");
        var o,
          a =
            (this && this.__extends) ||
            ((o = function (e, t) {
              return (o =
                Object.setPrototypeOf ||
                ({ __proto__: [] } instanceof Array &&
                  function (e, t) {
                    e.__proto__ = t;
                  }) ||
                function (e, t) {
                  for (var n in t) t.hasOwnProperty(n) && (e[n] = t[n]);
                })(e, t);
            }),
            function (e, t) {
              function n() {
                this.constructor = e;
              }
              o(e, t),
                (e.prototype =
                  null === t
                    ? Object.create(t)
                    : ((n.prototype = t.prototype), new n()));
            }),
          i =
            (this && this.__decorate) ||
            function (e, t, n, o) {
              var a,
                i = arguments.length,
                r =
                  i < 3
                    ? t
                    : null === o
                    ? (o = Object.getOwnPropertyDescriptor(t, n))
                    : o;
              if (
                "object" == typeof Reflect &&
                "function" == typeof Reflect.decorate
              )
                r = Reflect.decorate(e, t, n, o);
              else
                for (var s = e.length - 1; s >= 0; s--)
                  (a = e[s]) &&
                    (r = (i < 3 ? a(r) : i > 3 ? a(t, n, r) : a(t, n)) || r);
              return i > 3 && r && Object.defineProperty(t, n, r), r;
            };
        Object.defineProperty(n, "__esModule", { value: !0 });
        var r = e("../../Framework/Base/BaseComponent"),
          s = e("../../Framework/Enum/GameConst"),
          c = e("../../Framework/Enum/GameEnum"),
          l = e("../../Framework/Manager/AudioManager"),
          u = e("../../Framework/Manager/CirculateManager"),
          d = e("../../Framework/Manager/GameDataManager"),
          p = e("../../Framework/Manager/RoomInfoManager"),
          f = e("../../Framework/Manager/UserInfoManager"),
          h = e("../TurnHeadPhotoAnim"),
          g = cc._decorator,
          m = g.ccclass,
          _ = g.property,
          y = (function (e) {
            function t() {
              var t = (null !== e && e.apply(this, arguments)) || this;
              return (
                (t.node_my = null),
                (t.sprMyHeadPhoto = null),
                (t.labMyNickName = null),
                (t.nodePlayers = []),
                (t.label_name = []),
                (t.node_win_list = []),
                (t.node_win = null),
                (t.node_arrow = null),
                (t.node_lost1 = null),
                (t.node_win1 = null),
                (t.label_state = null),
                (t.moveTragetX = -225),
                (t.competitionList = []),
                t
              );
            }
            return (
              a(t, e),
              (t.prototype.onLoad = function () {
                (this.competitionList =
                  u.default.getInstance().competitionList),
                  this.showUI();
              }),
              (t.prototype.start = function () {}),
              (t.prototype.showUI = function () {
                var e = this;
                (this.node_lost1.active = 1 == this.competitionList.length),
                  this.showArrow(),
                  this.showFrame(),
                  this.setMyHeadPhoto(),
                  this.setMyNickName(),
                  this.node_my.runAction(
                    cc.sequence(
                      cc.delayTime(2),
                      cc.moveTo(1, cc.v2(this.moveTragetX, this.node_my.y)),
                      cc.delayTime(0.1),
                      cc.callFunc(function () {
                        for (var t = 0; t < e.nodePlayers.length; t++)
                          e.nodePlayers[t].active = !0;
                      }),
                      cc.delayTime(0.1),
                      cc.callFunc(function () {
                        e.matchOtherPlayers();
                      })
                    )
                  );
              }),
              (t.prototype.matchOtherPlayers = function () {
                var e = this;
                p.default.getInstance().setPlayerCount(4),
                  f.default.getInstance().generateGameUser(),
                  (d.default.getInstance().bomb = {});
                for (
                  var t = f.default.getInstance().getOhterUser(),
                    n = p.default.getInstance().getPlayerCount(),
                    o = 0,
                    a = function (a) {
                      i.loadRes(
                        s.HALL_PREFAB_PATH + "TurnHeadPhotoAnim",
                        cc.Prefab,
                        function (i) {
                          var r = null,
                            s = cc.instantiate(i),
                            l = s.getComponent(h.default);
                          n == c.PlayerCount.Two
                            ? ((s.parent = e.nodePlayers[1]),
                              (r =
                                e.nodePlayers[1].getChildByName("nodeSaoMiao")))
                            : ((s.parent = e.nodePlayers[a]),
                              (r =
                                e.nodePlayers[a].getChildByName(
                                  "nodeSaoMiao"
                                ))),
                            (r.zIndex = 10),
                            l.setInfo(
                              t[a].getNickName(),
                              t[a].getHeadPhotoIdx()
                            ),
                            l.startTurn(function () {
                              (r.active = !1),
                                (o += 1) == t.length && e.matchOver();
                            });
                        }
                      );
                    },
                    i = this,
                    r = 0;
                  r < t.length;
                  r++
                )
                  a(r);
              }),
              (t.prototype.matchOver = function () {
                p.default
                  .getInstance()
                  .setGameMode(u.default.getInstance().gameMode),
                  p.default.getInstance().setRoomMode(c.GameRoomMode.Quick),
                  d.default.getInstance().setFristEnterGame(!1),
                  p.default.getInstance().setEntryGold(0),
                  p.default
                    .getInstance()
                    .setComputerChessColor(c.ChessColor.Blue),
                  this.scheduleOnce(function () {
                    l.default.getInstance().stopAllAudio(),
                      cc.director.loadScene("Game_grass");
                  }, 0.01);
              }),
              (t.prototype.setMyHeadPhoto = function () {
                var e = this,
                  t = f.default
                    .getInstance()
                    .getMyselfUserInfo()
                    .getHeadPhotoIdx();
                this.loadRes(
                  s.PLAYER_HEAD_PHOTO_PATH + "img_head_photo_" + t,
                  cc.SpriteFrame,
                  function (t) {
                    e.sprMyHeadPhoto.spriteFrame = t;
                  }
                );
              }),
              (t.prototype.setMyNickName = function () {
                this.labMyNickName.string = f.default
                  .getInstance()
                  .getMyselfUserInfo()
                  .getNickName();
              }),
              (t.prototype.showArrow = function () {
                for (
                  var e = "", t = [], n = 0;
                  n < this.competitionList.length;
                  n++
                )
                  t.push(this.competitionList[n]);
                for (
                  t.sort(function (e, t) {
                    return e - t;
                  }),
                    n = 0;
                  n < t.length;
                  n++
                )
                  e += t[n];
                console.log("arrowName:" + e);
                var o = 1 == t[0] ? "img_win" : "img_lost",
                  a = this.node_arrow.getChildByName(o + e);
                a && (a.active = !0);
              }),
              (t.prototype.showFrame = function () {
                this.competitionList.length;
                for (
                  var e =
                      1 ==
                      this.competitionList[this.competitionList.length - 1],
                    t = [],
                    n = 0;
                  n < this.competitionList.length;
                  n++
                )
                  t.push(this.competitionList[n]);
                var o = "",
                  a = function (e) {
                    o += t[e];
                    var n = i.competitionList[e],
                      a = u.default.getInstance().First
                        ? "img_win"
                        : "img_lost",
                      r = i.node_win
                        .getChildByName(a + o)
                        .getComponent(cc.Sprite);
                    if (t.length - 1 == e) {
                      var s = i.node_win.getChildByName(a + o + "1");
                      if (s) {
                        var c = s.getChildByName("node_win");
                        (c.active = !0),
                          c.getComponent(cc.Animation).play("huxi");
                      }
                    }
                    (r.node.active = !0), (r.node.zIndex = 2);
                    var l;
                    console.log("num:  " + o),
                      (l =
                        u.default.getInstance().First &&
                        1 == i.competitionList[e]
                          ? 0 == e
                            ? "img_right_win"
                            : 0 != e &&
                              -1 != i.competitionList.indexOf(0) &&
                              1 != e
                            ? "img_right_win"
                            : "img_left_win"
                          : 1 == n
                          ? "img_right_win"
                          : "img_left_lost"),
                      i.loadRes(l, cc.SpriteFrame, function (e) {
                        r.spriteFrame = e;
                      });
                  },
                  i = this;
                for (n = 0; n < t.length; n++) a(n);
                (this.label_state.string = e ? "Win" : "Lost"),
                  (this.label_state.node.color = e
                    ? cc.color(254, 199, 0)
                    : cc.color(194, 194, 194));
              }),
              i([_(cc.Node)], t.prototype, "node_my", void 0),
              i([_(cc.Sprite)], t.prototype, "sprMyHeadPhoto", void 0),
              i([_(cc.Label)], t.prototype, "labMyNickName", void 0),
              i([_(cc.Node)], t.prototype, "nodePlayers", void 0),
              i([_(cc.Label)], t.prototype, "label_name", void 0),
              i([_(cc.Sprite)], t.prototype, "node_win_list", void 0),
              i([_(cc.Node)], t.prototype, "node_win", void 0),
              i([_(cc.Node)], t.prototype, "node_arrow", void 0),
              i([_(cc.Node)], t.prototype, "node_lost1", void 0),
              i([_(cc.Node)], t.prototype, "node_win1", void 0),
              i([_(cc.Label)], t.prototype, "label_state", void 0),
              i([m], t)
            );
          })(r.default);
        (n.default = y), cc._RF.pop();
      },
      {
        "../../Framework/Base/BaseComponent": "BaseComponent",
        "../../Framework/Enum/GameConst": "GameConst",
        "../../Framework/Enum/GameEnum": "GameEnum",
        "../../Framework/Manager/AudioManager": "AudioManager",
        "../../Framework/Manager/CirculateManager": "CirculateManager",
        "../../Framework/Manager/GameDataManager": "GameDataManager",
        "../../Framework/Manager/RoomInfoManager": "RoomInfoManager",
        "../../Framework/Manager/UserInfoManager": "UserInfoManager",
        "../TurnHeadPhotoAnim": "TurnHeadPhotoAnim",
      },
    ],
    "use_v2.1-2.2.1_cc.Toggle_event": [
      function (e, t) {
        "use strict";
        cc._RF.push(
          t,
          "9950bFGN5tLPJC3oApRRoWJ",
          "use_v2.1-2.2.1_cc.Toggle_event"
        ),
          cc.Toggle && (cc.Toggle._triggerEventInScript_isChecked = !0),
          cc._RF.pop();
      },
      {},
    ],
  },
  {},
  [
    "AdLoading",
    "CoinsFlyEffect",
    "ColorAssembler2d",
    "Dice",
    "Tips",
    "Tools",
    "EntryScene",
    "BaseComponent",
    "GameConst",
    "GameEnum",
    "AtlasResManager",
    "AudioManager",
    "BuriedPointManager",
    "ChessManager",
    "CirculateManager",
    "GameDataManager",
    "GlobalTimerManager",
    "LuckManager",
    "MapGridManager",
    "RobotManager",
    "RoomInfoManager",
    "ShopDataManager",
    "TaskManager",
    "UserInfoManager",
    "H5Test",
    "NativeBridge",
    "StrategyManager",
    "Utils",
    "Add_Player",
    "Add_Player_Tips",
    "Chess",
    "GameMatch",
    "GameScene",
    "GameSettlementView",
    "MapGrid",
    "PlayerInfo",
    "QuitGameSettingView",
    "QuitGameView",
    "QuitPrizeView",
    "SettlementItem",
    "UndoDice",
    "UndoHelp",
    "Upgrade",
    "UsePropsView",
    "expressionView",
    "DiceTestUI",
    "ADRewardView",
    "CoinsNotEnoughView",
    "GameSettingView",
    "HallScene",
    "HeadPhotoItem",
    "LocalRoomView",
    "MatchPlayerView",
    "ModifyCountryView",
    "ModifyHeadPhotoView",
    "NoNetworkView",
    "OnlineRewardView",
    "SignView",
    "TimingBoxDealsItem",
    "TransitionView",
    "TurnHeadPhotoAnim",
    "UpgradeRewardView",
    "UserInfoView",
    "WatchADOutView",
    "activityCell",
    "activityHelp",
    "activityMatchPlayerView",
    "activityView",
    "bombResult",
    "boxRewardCell",
    "cupPoster",
    "promotionView",
    "addGuideView",
    "computerPlayCountView",
    "computerRoomView",
    "newPlayReward",
    "newRoomInfoView",
    "GetRewardView",
    "RewardDoubleView",
    "TurntableView",
    "CountryItem",
    "LoginScene",
    "NetInterface",
    "NetManager",
    "NetNode",
    "WebSock",
    "NodePool",
    "ResKeeper",
    "ResLeakChecker",
    "ResLoader",
    "ResManager",
    "ResPool",
    "ResUtil",
    "use_v2.1-2.2.1_cc.Toggle_event",
  ]
);
