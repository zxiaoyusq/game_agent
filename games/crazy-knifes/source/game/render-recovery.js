(function (root) {
    'use strict';
    var app, forceUntil = 0, lastFrame = 0, lastWake = -1000, rendered = false;
    var now = function () { return performance.now(); };
    function wake() {
        if (!app || document.hidden) return;
        var time = now();
        forceUntil = time + 350;
        app.renderNextFrame = true;
        lastWake = time;
    }
    root.CrazyKnifesRenderRecovery = {
        attach: function (application) {
            app = application;
            lastFrame = now();
            app.on('postrender', function () { rendered = true; lastFrame = now(); });
            ['focus', 'pageshow', 'resize', 'orientationchange', 'pointerdown', 'touchstart'].forEach(function (event) {
                root.addEventListener(event, wake, { passive: true });
            });
            document.addEventListener('visibilitychange', wake);
            app.graphicsDevice.canvas.addEventListener('webglcontextrestored', wake);
            // A paused game must keep drawing menus. Recover a missed render
            // request without reloading the page or changing gameplay state.
            var timer = setInterval(function () {
                var time = now();
                if (rendered && !document.hidden && time - lastFrame > 1500 && time - lastWake > 1000) wake();
            }, 500);
            app.once('destroy', function () { clearInterval(timer); });
        },
        wake: wake,
        forceFrame: function (time) { return time < forceUntil; }
    };
}(window));
