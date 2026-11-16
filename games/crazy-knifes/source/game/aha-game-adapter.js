(function (global) {
    'use strict';
    let active = null;
    let externalState = null;
    let readySent = false;
    const origin = global.location.origin;

    function parentWindow() {
        try {
            if (global.parent !== global && global.parent.location.origin === origin) return global.parent;
        } catch (_) {}
        return null;
    }

    function pause() {
        const game = global.Game && global.Game.instance;
        if (!game) return null;
        const input = global.Input;
        const audio = global.GameAudio;
        const state = {
            game, paused: game.paused, controls: game.controlsEnabled,
            inputDisabled: input && input.mouseDis,
            physics: game.app.systems.rigidbody.fixedTimeStep,
            timeScale: game.app.timeScale,
            mute: audio && audio.mute, muteMusic: audio && audio.muteMus
        };
        game.pause(true);
        game.controlsEnabled = false;
        game.app.timeScale = 0;
        if (input) {
            input.mouseDis = true;
            input.mouseDown = false;
            if (input.flushPresses) input.flushPresses();
        }
        if (audio) { audio.switch(true); audio.switchMusic(true); }
        return state;
    }

    function restore(state) {
        if (!state || !global.Game || global.Game.instance !== state.game) return;
        const game = state.game;
        game.pause(state.paused);
        game.app.systems.rigidbody.fixedTimeStep = state.physics;
        game.app.timeScale = state.timeScale;
        game.controlsEnabled = state.controls;
        if (global.Input) {
            global.Input.mouseDis = state.inputDisabled;
            global.Input.mouseDown = false;
            if (global.Input.flushPresses) global.Input.flushPresses();
        }
        if (global.GameAudio) {
            global.GameAudio.switch(state.mute);
            global.GameAudio.switchMusic(state.muteMusic);
        }
        if (global.CrazyKnifesRenderRecovery) global.CrazyKnifesRenderRecovery.wake();
    }

    function notifyFailure(status) {
        if (typeof global.showMessage !== 'function') return;
        const message = status === 'dismissed' ? 'Reward canceled' : 'Failed to get the reward, please try again later.';
        global.showMessage(message);
    }

    class AhaGameSDKHandler {
        constructor() { this.sdkLoaded = false; this.onSDKReady = null; }
        async initSDK() {
            // Engine boot is local. Ad availability is checked for each request.
            this.sdkLoaded = true;
            if (this.onSDKReady) this.onSDKReady();
        }
        setSDKReadyCallback(callback) { this.onSDKReady = callback; }
        preventDefaultScroll() {
            global.addEventListener('wheel', event => event.preventDefault(), {passive: false});
            global.addEventListener('keydown', event => {
                if (['ArrowUp', 'ArrowDown', ' '].includes(event.key)) event.preventDefault();
            });
        }
        requestAd(type, rewardCallback) {
            void 0;
            const rewarded = type === 'rewarded';
            if (active || externalState) return Promise.resolve(false);
            const parent = parentWindow();
            if (!readySent || !parent || !parent.CrazyKnifesAhaHost || !parent.CrazyKnifesAhaHost.ready) {
                void 0;
                if (rewarded) notifyFailure('notReady');
                return Promise.resolve(false);
            }
            const slot = rewarded ? 'MIAD' : 'MIAD_NEXT';
            return new Promise(resolve => {
                const request = {state: pause(), timer: null, done: false, callbacks: null};
                active = request;
                function settle(success, status) {
                    if (request.done || active !== request) return;
                    request.done = true;
                    void 0;
                    global.clearTimeout(request.timer);
                    // Keep inert callbacks for any already queued host message.
                    if (parent[slot] === request.callbacks) parent[slot] = {_callback() {}, _failback() {}};
                    restore(request.state);
                    // Hold the request lock through the reward's synchronous side effects.
                    try {
                        if (rewarded && success && typeof rewardCallback === 'function') rewardCallback();
                        else if (rewarded && !success) notifyFailure(status);
                    } catch (error) { console.error('[AHA reward callback]', error); }
                    finally { active = null; resolve(success); }
                }
                request.callbacks = {
                    _callback: () => settle(true, 'viewed'),
                    _failback: status => settle(false, status || 'error')
                };
                parent[slot] = request.callbacks;
                request.timer = global.setTimeout(() => settle(false, 'timeout'), 125000);
                try { parent.postMessage(rewarded ? 'reward' : 'next', origin); }
                catch (_) { settle(false, 'error'); }
            });
        }
        checkEnvironment() {}
        async getUserData() { return null; }
        isQATool() { return false; }
        gameplayStop() {}
        gameplayStart() {}
        celebrateHappyTime() {}
        startGameLoading() {}
        stopGameLoading() {}
    }

    global.CrazyKnifesAhaHandler = AhaGameSDKHandler;
    global.CrazyKnifesAhaClient = Object.freeze({
        markReady() {
            if (readySent) return;
            readySent = true;
            const parent = parentWindow();
            if (parent) parent.postMessage('gameLoadingCompleted', origin);
        },
        beginExternalAd() {
            if (!externalState && !active) externalState = pause();
        },
        endExternalAd() {
            const state = externalState;
            externalState = null;
            restore(state);
        }
    });
})(window);
