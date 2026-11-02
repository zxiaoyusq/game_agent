package com.kumobius.android.features;

import android.app.Activity;
import android.util.Log;
import android.view.Gravity;
import android.widget.FrameLayout;

import com.hisavana.common.bean.TAdErrorCode;
import com.hisavana.common.bean.TAdRequestBody;
import com.hisavana.common.interfacz.TAdListener;
import com.hisavana.mediation.ad.TInterstitialAd;
import com.hisavana.mediation.ad.TRewardedAd;
import com.hisavana.mediation.config.TAdManager;

/**
 * Wall Kickers 广告 Feature：Hisavana 实现，替换 AdsFeatures(AppLovin/ironSource/Unity/Fyber)。
 * 契约来源：com.kumobius.android.features.IAdsFeature（19 方法） 见 ../feature_api.json
 * 参考实现：传音素材包 bridge_reference/HisavanaSDK.java  GameTRewardedAd.java  GameTInterstitialAd.java
 *
 * 语义映射（依据 AdsFeatures 的反编译事实）：
 *   incentivised = 激励视频（原 MyMaxRewardedAdListener）
 *   video        = 插屏（原 MyMaxAdListener）
 *
 * TODO(接入前必须提供)：
 *   [1] HISAVANA_APP_ID  [2] SLOT_REWARDED  [3] SLOT_INTERSTITIAL  [4] OFFLINE_ID(内部默认广告版本，可空)
 *   [5] 若启用 Banner：SLOT_BANNER + 容器尺寸策略
 */
public class HisavanaAdsFeature implements IAdsFeature {

    private static final String TAG = "WjHisavanaAds";

    /** 以下 4 个值由发布方在 Hisavana 控制台申请后填入（勿照抄 BlockMaster 的值）。 */
    private static final String HISAVANA_APP_ID = "REPLACE_ME";
    private static final String SLOT_REWARDED = "REPLACE_ME";
    private static final String SLOT_INTERSTITIAL = "REPLACE_ME";
    private static final long OFFLINE_ID = 0L;

    private final Activity activity;
    private TRewardedAd rewarded;
    private TInterstitialAd interstitial;
    private FrameLayout bannerContainer;

    private volatile boolean rewardReady, rewardPlaying, rewardLoading;
    private volatile boolean interstitialReady, interstitialPlaying, interstitialLoading;
    private volatile boolean rewardEnabled = true, videoEnabled = true;

    public HisavanaAdsFeature(Activity activity) {
        this.activity = activity;
    }

    // ---------------- IAdsFeature: 生命周期 ----------------

    @Override public void adsInit() {
        activity.runOnUiThread(new Runnable() {
            @Override public void run() {
                try {
                    TAdManager.init(activity, new TAdManager.AdConfigBuilder()
                            .setAppId(HISAVANA_APP_ID)
                            .setDebug(false)
                            .testDevice(false)
                            .setMuteVideo(false)
                            .isInitAdMob(true)                       // 视投放的广告源调整
                            .setInternalDefaultAdVersion(OFFLINE_ID)
                            .setCloudCompleteListener(new TAdManager.OnCloudCompleteListener() {
                                @Override public void onCloudComplete(int code, String msg) {
                                    Log.i(TAG, "onCloudComplete code=" + code + " msg=" + msg);
                                    // 建议：code==0 后再触发首次 load（本类已按需 load，无需强依赖）
                                }
                            })
                            .build());
                } catch (Throwable t) {
                    Log.e(TAG, "TAdManager.init failed", t);
                }
            }
        });
    }

    @Override public void adsOnStart()   { /* Hisavana 自行处理前后台，保留钩子 */ }
    @Override public void adsOnStop()    { }
    @Override public void adsOnResume()  { }
    @Override public void adsOnPause()   { }
    @Override public void adsOnDestroy() {
        if (rewarded != null) { rewarded.destroy(); rewarded = null; }
        if (interstitial != null) { interstitial.destroy(); interstitial = null; }
        if (bannerContainer != null) { bannerContainer.removeAllViews(); bannerContainer = null; }
    }
    @Override public boolean adsOnBackPressed() { return false; }   // 交回游戏处理
    @Override public void adsShowDebugUi() { Log.i(TAG, "rewardReady=" + rewardReady + " interReady=" + interstitialReady); }
    @Override public String adsGetSystemName() { return "hisavana"; }

    // ---------------- IAdsFeature: 激励视频 ----------------

    @Override public void adsRequestIncentivisedAd() {
        if (rewardLoading || rewardPlaying) return;
        if (rewarded != null && rewarded.hasAd()) { rewardReady = true; return; }
        rewardLoading = true;
        activity.runOnUiThread(new Runnable() {
            @Override public void run() {
                try {
                    if (rewarded != null) { rewarded.destroy(); rewarded = null; }
                    rewarded = new TRewardedAd(activity, SLOT_REWARDED);
                    rewarded.setRequestBody(new TAdRequestBody.AdRequestBodyBuild()
                            .setAdListener(rewardLoadListener).build());
                    rewarded.loadAd();
                } catch (Throwable t) {
                    rewardLoading = false; rewardReady = false;
                    Log.e(TAG, "load rewarded failed", t);
                }
            }
        });
    }

    @Override public boolean adsGetIncentivisedAdReady()   { return rewardEnabled && rewardReady && rewarded != null && rewarded.hasAd(); }
    @Override public boolean adsGetIncentivisedAdPlaying() { return rewardPlaying; }
    @Override public boolean adsGetIncentivisedAdsEnabled(){ return rewardEnabled; }
    @Override public void adsSetIncentivisedAdsEnabled(boolean enabled) { rewardEnabled = enabled; }

    /** native 侧"请求即播放"的调用点：ready 时直接 show，否则 load 后自动 show。 */
    public void requestOrShowRewarded(final String scene) {
        if (adsGetIncentivisedAdReady()) { showRewarded(scene); return; }
        adsRequestIncentivisedAd();
        rewardAutoScene = scene;
    }
    private String rewardAutoScene;

    private void showRewarded(final String scene) {
        rewardPlaying = true;
        activity.runOnUiThread(new Runnable() {
            @Override public void run() {
                try {
                    rewarded.setRequestBody(new TAdRequestBody.AdRequestBodyBuild()
                            .setAdListener(rewardShowListener).build());
                    String token = rewarded.enterScene(scene, 1);
                    rewarded.show(activity, token);
                } catch (Throwable t) {
                    rewardPlaying = false;
                    Log.e(TAG, "show rewarded failed", t);
                }
            }
        });
    }

    private final TAdListener rewardLoadListener = new TAdListener() {
        @Override public void onLoad() { rewardLoading = false; rewardReady = true;
            if (rewardAutoScene != null) { String s = rewardAutoScene; rewardAutoScene = null; showRewarded(s); } }
        @Override public void onError(TAdErrorCode code) { rewardLoading = false; rewardReady = false; Log.w(TAG, "reward load error: " + code); }
        @Override public void onClicked(int i) { }
        @Override public void onClosed(int i) { }
        @Override public void onRewarded() { }
        @Override public void onShow(int i) { }
        @Override public void onShowError(TAdErrorCode code) { }
    };

    private final TAdListener rewardShowListener = new TAdListener() {
        @Override public void onLoad() { }
        @Override public void onError(TAdErrorCode code) { rewardPlaying = false; Log.w(TAG, "reward show error: " + code); }
        @Override public void onClicked(int i) { }
        @Override public void onClosed(int i) { rewardPlaying = false; rewardReady = false; }
        @Override public void onRewarded() { /* 发奖回调：如需额外埋点在此上报 */ }
        @Override public void onShow(int i) { }
        @Override public void onShowError(TAdErrorCode code) { rewardPlaying = false; Log.w(TAG, "reward onShowError: " + code); }
    };

    // ---------------- IAdsFeature: 插屏（游戏里叫 video） ----------------

    @Override public void adsRequestVideoAd() {
        if (interstitialLoading || interstitialPlaying) return;
        if (interstitial != null && interstitial.hasAd()) { interstitialReady = true; return; }
        interstitialLoading = true;
        activity.runOnUiThread(new Runnable() {
            @Override public void run() {
                try {
                    if (interstitial != null) { interstitial.destroy(); interstitial = null; }
                    interstitial = new TInterstitialAd(activity, SLOT_INTERSTITIAL);
                    interstitial.setRequestBody(new TAdRequestBody.AdRequestBodyBuild()
                            .setAdListener(interLoadListener).build());
                    interstitial.loadAd();
                } catch (Throwable t) {
                    interstitialLoading = false; interstitialReady = false;
                    Log.e(TAG, "load interstitial failed", t);
                }
            }
        });
    }

    @Override public boolean adsGetVideoAdReady()   { return videoEnabled && interstitialReady && interstitial != null && interstitial.hasAd(); }
    @Override public boolean adsGetVideoAdPlaying() { return interstitialPlaying; }
    @Override public boolean adsGetVideoAdsEnabled(){ return videoEnabled; }
    @Override public void adsSetVideoAdsEnabled(boolean enabled) { videoEnabled = enabled; }

    public void requestOrShowInterstitial(final String scene) {
        if (adsGetVideoAdReady()) { showInterstitial(scene); return; }
        adsRequestVideoAd();
        interstitialAutoScene = scene;
    }
    private String interstitialAutoScene;

    private void showInterstitial(final String scene) {
        interstitialPlaying = true;
        activity.runOnUiThread(new Runnable() {
            @Override public void run() {
                try {
                    interstitial.setRequestBody(new TAdRequestBody.AdRequestBodyBuild()
                            .setAdListener(interShowListener).build());
                    String token = interstitial.enterScene(scene, 1);
                    interstitial.show(activity, token);
                } catch (Throwable t) {
                    interstitialPlaying = false;
                    Log.e(TAG, "show interstitial failed", t);
                }
            }
        });
    }

    private final TAdListener interLoadListener = new TAdListener() {
        @Override public void onLoad() { interstitialLoading = false; interstitialReady = true;
            if (interstitialAutoScene != null) { String s = interstitialAutoScene; interstitialAutoScene = null; showInterstitial(s); } }
        @Override public void onError(TAdErrorCode code) { interstitialLoading = false; interstitialReady = false; Log.w(TAG, "inter load error: " + code); }
        @Override public void onClicked(int i) { }
        @Override public void onClosed(int i) { }
        @Override public void onRewarded() { }
        @Override public void onShow(int i) { }
        @Override public void onShowError(TAdErrorCode code) { }
    };

    private final TAdListener interShowListener = new TAdListener() {
        @Override public void onLoad() { }
        @Override public void onError(TAdErrorCode code) { interstitialPlaying = false; Log.w(TAG, "inter show error: " + code); }
        @Override public void onClicked(int i) { }
        @Override public void onClosed(int i) { interstitialPlaying = false; interstitialReady = false; }
        @Override public void onRewarded() { }
        @Override public void onShow(int i) { }
        @Override public void onShowError(TAdErrorCode code) { interstitialPlaying = false; Log.w(TAG, "inter onShowError: " + code); }
    };
}
