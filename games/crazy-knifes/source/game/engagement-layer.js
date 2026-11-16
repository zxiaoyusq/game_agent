(function () {
    'use strict';

    var root = null;
    var toastTimer = 0;
    var lastState = null;
    function ensureHud() {
        if (root && root.isConnected) return root;
        if (!document.body) return null;

        if (!document.getElementById('sm-engagement-style')) {
            var style = document.createElement('style');
            style.id = 'sm-engagement-style';
            style.textContent = [
                '#sm-engagement-hud{position:fixed;bottom:calc(env(safe-area-inset-bottom,0px) + 10px);left:50%;transform:translateX(-50%);z-index:9999998;width:min(560px,86vw);font-family:"Nirmala UI","Noto Sans Devanagari","Noto Sans Bengali",system-ui,Arial,sans-serif;color:#fff;text-align:center;pointer-events:none;filter:drop-shadow(0 2px 3px rgba(0,0,0,.28))}',
                '#sm-engagement-hud .sm-row{display:flex;align-items:center;justify-content:center;gap:8px}',
                '#sm-engagement-hud .sm-pill{box-sizing:border-box;flex:0 1 auto;min-width:max-content;background:rgba(16,33,53,.82);border:2px solid rgba(255,255,255,.78);border-radius:999px;padding:6px 13px;font-size:clamp(12px,1.45vw,20px);font-weight:800;line-height:1.15;letter-spacing:.1px;white-space:nowrap;overflow:visible}',
                '#sm-engagement-hud .sm-goal{margin-top:6px;background:rgba(16,33,53,.78);border-radius:11px;padding:6px 9px}',
                '#sm-engagement-hud .sm-goal-copy{display:flex;justify-content:space-between;gap:10px;font-size:clamp(11px,1.25vw,17px);font-weight:800}',
                '#sm-engagement-hud .sm-track{height:6px;margin-top:5px;border-radius:8px;overflow:hidden;background:rgba(255,255,255,.25)}',
                '#sm-engagement-hud .sm-fill{height:100%;width:0;background:linear-gradient(90deg,#62e8ff,#fff45d);transition:width .18s ease-out}',
                '#sm-engagement-toast{position:fixed;left:50%;top:24%;transform:translate(-50%,-50%) scale(.92);z-index:9999999;padding:12px 20px;border-radius:14px;background:rgba(17,34,52,.88);border:2px solid rgba(255,255,255,.85);font-family:Arial,sans-serif;color:#fff;font-size:clamp(18px,2.4vw,34px);font-weight:900;text-align:center;pointer-events:none;opacity:0;transition:opacity .16s ease,transform .16s ease}',
                '#sm-engagement-toast.sm-show{opacity:1;transform:translate(-50%,-50%) scale(1)}',
                '@media(max-width:420px){#sm-engagement-hud{width:88vw}.sm-goal-copy{white-space:nowrap;overflow:hidden}}'
            ].join('');
            document.head.appendChild(style);
        }

        root = document.createElement('div');
        root.id = 'sm-engagement-hud';
        root.setAttribute('aria-live', 'polite');
        root.innerHTML = '<div class="sm-row"><div class="sm-pill sm-level"></div><div class="sm-pill sm-bonus"></div></div><div class="sm-goal"><div class="sm-goal-copy"><span class="sm-goal-title"></span><span class="sm-goal-progress"></span></div><div class="sm-track"><div class="sm-fill"></div></div></div>';
        document.body.appendChild(root);
        return root;
    }

    function render(state) {
        lastState = state;
        var hud = ensureHud();
        if (!hud) return;
        hud.style.display = '';
        hud.dataset.level = String(state.level);
        hud.dataset.bonus = state.bonus;
        hud.dataset.goal = state.goal;
        hud.querySelector('.sm-level').textContent = state.levelLabel;
        hud.querySelector('.sm-bonus').textContent = state.bonus;
        hud.querySelector('.sm-goal-title').textContent = state.goal;
        hud.querySelector('.sm-goal-progress').textContent = state.progressLabel;
        hud.querySelector('.sm-fill').style.width = Math.max(0, Math.min(100, state.progress * 100)) + '%';
        hud.querySelector('.sm-row').style.display = '';
        hud.querySelector('.sm-goal').style.display = '';
    }

    function toast(message) {
        ensureHud();
        var el = document.getElementById('sm-engagement-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'sm-engagement-toast';
            document.body.appendChild(el);
        }
        el.textContent = message;
        el.classList.add('sm-show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { el.classList.remove('sm-show'); }, 1800);
    }

    window.CrazyKnifesEngagementHUD = {
        set: render,
        hide: function () {
            var hud = ensureHud();
            if (!hud) return;
            hud.style.display = 'none';
        },
        toast: toast,
        getState: function () { return lastState; }
    };
}());
