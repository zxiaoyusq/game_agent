/* AHA host bridge for the supplied Crazy Knifes template (app key 5027208).
 * Serve this shell and game/ from one HTTP(S) origin. No local success simulator.
 */
(function () {
    'use strict';

    var iframe = document.getElementById('iframe');
    if (!iframe) throw new Error('Crazy Knifes: game iframe is missing.');

    var SDK_URL = 'https://www.hippoobox.com/static/sdk/adsdk_1.8.0.0.js';
    var AD_TIMEOUT_MS = 120000;
    var sdkInitialized = false;
    var sdkUnavailable = false;
    var adReady = false;
    var childReady = false;
    var loadingReported = false;
    var prerollDecided = false;
    var adsConfigured = false;
    var gameStartSent = false;
    var activeAd = null;
    var origin = window.location.origin;

    // Only readiness is public. Settlement and reward callbacks stay private.
    var publicState = {};
    Object.defineProperty(publicState, 'ready', {
        enumerable: true,
        get: function () { return sdkInitialized && adReady && !sdkUnavailable; }
    });
    Object.freeze(publicState);
    Object.defineProperty(window, 'CrazyKnifesAhaHost', {
        value: publicState,
        writable: false,
        configurable: false,
        enumerable: true
    });

    function warn(message, error) {
        if (window.console && typeof console.warn === 'function') {
            console.warn('[Crazy Knifes AHA] ' + message, error || '');
        }
    }

    function callResult(callbacks, succeeded, status) {
        if (!callbacks) return;
        var callback = succeeded ? callbacks._callback : callbacks._failback;
        if (typeof callback !== 'function') return;
        try {
            callback(status);
        } catch (error) {
            warn('The game callback threw an error.', error);
        }
    }

    function endExternalAd(request) {
        if (!request.externalClient) return;
        var client = request.externalClient;
        request.externalClient = null;
        try {
            client.endExternalAd();
        } catch (error) {
            warn('Could not restore the game after preroll.', error);
        }
    }

    function finishAd(request, succeeded, status) {
        if (!request.settled) void 0;
        if (request.settled) return;
        request.settled = true;
        window.clearTimeout(request.timer);
        endExternalAd(request);
        if (activeAd === request) activeAd = null;
        if (request.type !== 'preroll') {
            callResult(request.callbacks, succeeded, status);
        }
    }

    function reportLoadingCompleted() {
        if (!childReady || !sdkInitialized || sdkUnavailable || loadingReported) return;
        loadingReported = true;
        try {
            window.h5sdk.gameLoadingCompleted();
        } catch (error) {
            warn('Loading completion could not be reported.', error);
        }
    }

    function requestAd(type, callbacks) {
        void 0;
        // Capture the caller's object now. A late SDK result must never resolve
        // a subsequent request by reading a newer window.MIAD callback slot.
        if (type !== 'preroll' && (!callbacks || typeof callbacks._callback !== 'function' ||
            typeof callbacks._failback !== 'function')) {
            warn('Ignoring an advertisement request without its game callbacks.');
            return;
        }
        if (!sdkInitialized || !adReady || sdkUnavailable) {
            callResult(callbacks, false, sdkUnavailable ? 'sdkUnavailable' : 'notReady');
            return;
        }
        if (activeAd) {
            // A duplicate message for the same request must not fail the
            // already-running request through its own callback object.
            if (activeAd.callbackOwner === callbacks) return;
            callResult(callbacks, false, 'busy');
            return;
        }

        var request = {
            type: type,
            callbackOwner: callbacks,
            callbacks: callbacks ? { _callback: callbacks._callback, _failback: callbacks._failback } : null,
            settled: false,
            externalClient: null,
            timer: null
        };
        activeAd = request;
        request.timer = window.setTimeout(function () {
            finishAd(request, false, 'timeout');
        }, AD_TIMEOUT_MS);

        var options = {
            type: type,
            name: type === 'reward' ? 'myreward' : type === 'next' ? 'mynext' : 'mypreroll',
            adBreakDone: function (info) {
                var status = info && typeof info.breakStatus === 'string' ? info.breakStatus : 'error';
                finishAd(request, status === 'viewed', status);
            }
        };
        if (type === 'preroll') {
            // The Ad Placement API forbids beforeAd/afterAd on preroll.
            // The game has finished loading here, so pause it directly and
            // restore it from finishAd on every completion/failure path.
            try {
                var client = iframe.contentWindow.CrazyKnifesAhaClient;
                if (client && typeof client.beginExternalAd === 'function' &&
                    typeof client.endExternalAd === 'function') {
                    request.externalClient = client;
                    client.beginExternalAd();
                }
            } catch (error) {
                warn('Could not pause the game for preroll.', error);
            }
        } else {
            options.beforeAd = function () {};
            options.afterAd = function () {};
        }
        if (type === 'reward') {
            options.beforeReward = function (showAd) {
                if (!request.settled && typeof showAd === 'function') showAd();
            };
        }

        try {
            window.h5sdk.adBreak(options);
        } catch (error) {
            warn('Advertising request failed.', error);
            finishAd(request, false, 'error');
        }
    }

    function decidePreroll() {
        if (prerollDecided) return;
        prerollDecided = true;
        // A late SDK must not interrupt a player who has already started.
        // Make this decision only when the child first reports real readiness.
        if (!sdkInitialized || !adReady || sdkUnavailable || activeAd) return;
        try {
            var client = iframe.contentWindow.CrazyKnifesAhaClient;
            if (!client || typeof client.beginExternalAd !== 'function' ||
                typeof client.endExternalAd !== 'function') return;
        } catch (error) {
            return;
        }
        requestAd('preroll', null);
    }

    window.addEventListener('message', function (event) {
        if (event.source !== iframe.contentWindow || event.origin !== origin) return;
        if (event.data === 'gameLoadingCompleted') {
            if (childReady) return;
            childReady = true;
            reportLoadingCompleted();
            decidePreroll();
        } else if (event.data === 'reward') {
            requestAd('reward', window.MIAD);
        } else if (event.data === 'next') {
            requestAd('next', window.MIAD_NEXT);
        }
    });

    function disableSdk(error) {
        sdkUnavailable = true;
        adReady = false;
        warn('SDK is unavailable; the game remains playable.', error);
        if (activeAd) finishAd(activeAd, false, 'sdkUnavailable');
    }

    function configureAds() {
        if (adsConfigured || sdkUnavailable) return;
        // The supplied SDK registers the advertising API during init(), not
        // when its script first loads. Validate it at its advertised callback.
        if (!window.h5sdk || typeof window.h5sdk.adBreak !== 'function' ||
            typeof window.h5sdk.adConfig !== 'function') {
            disableSdk(new Error('AHA advertising API was not registered during initialization.'));
            return;
        }
        adsConfigured = true;
        sdkInitialized = true;
        void 0;
        reportLoadingCompleted();
        if (!gameStartSent) {
            gameStartSent = true;
            try {
                window.h5sdk.athenaSend('game_start');
            } catch (error) {
                warn('The game_start event could not be sent.', error);
            }
        }
        try {
            window.h5sdk.adConfig({
                preloadAdBreaks: 'on',
                onReady: function () {
                    if (!sdkUnavailable) { adReady = true; void 0; }
                    // No preroll here: it must never appear late.
                }
            });
        } catch (error) {
            disableSdk(error);
        }
    }

    function initializeSdk() {
        try {
            var sdk = window.h5sdk;
            if (!sdk || typeof sdk.init !== 'function' || typeof sdk.gameLoadingCompleted !== 'function') {
                throw new Error('The supplied AHA SDK API did not load.');
            }
            var result = sdk.init(5027208, '', '', '', '', {
                ga: { id: 'G-L2NLPJNTLS' },
                adsence: {
                    client: 'ca-pub-3214612466403714',
                    'data-ad-frequency-hint': '45s',
                    'data-ad-channel': '8536733430',
                    callback: configureAds
                }
            });
            if (result && typeof result.then === 'function') {
                result.then(function () {
                    if (sdkUnavailable) return;
                    sdkInitialized = true;
                    reportLoadingCompleted();
                }, disableSdk);
            } else {
                sdkInitialized = true;
                reportLoadingCompleted();
            }
        } catch (error) {
            disableSdk(error);
        }
    }

    // Listener registration above must precede the game navigation. The game
    // is deliberately independent of the remote SDK script's load event.
    iframe.src = './game/index.html';
    if (window.location.protocol !== 'http:' && window.location.protocol !== 'https:') {
        disableSdk(new Error('Use an HTTP(S) server; file:// is not supported.'));
        return;
    }

    window.adsbygoogle = window.adsbygoogle || [];
    window.adsbygoogle.push({});
    var script = document.createElement('script');
    script.src = SDK_URL;
    script.async = true;
    script.onload = function () {
        // Preserve the supplied template's native a_bridge initialization
        // boundary while leaving ordinary Web initialization independent.
        if (window.a_bridge && document.readyState !== 'complete') {
            window.addEventListener('load', initializeSdk, { once: true });
        } else {
            initializeSdk();
        }
    };
    script.onerror = function () { disableSdk(new Error('AHA SDK script could not be loaded.')); };
    document.head.appendChild(script);
}());
