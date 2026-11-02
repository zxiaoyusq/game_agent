package com.kumobius.android.features;

import android.content.Context;
import android.os.Bundle;
import android.util.Log;

import com.transsion.ga.AthenaAnalytics;

import org.json.JSONObject;

import java.util.Map;

/**
 * Wall Kickers 埋点 Feature：Athena 实现，替换原 IAnalyticsFeature 实现。
 * 契约来源：com.kumobius.android.features.IAnalyticsFeature（7 方法） 见 ../feature_api.json
 * 参考实现：传音素材包 bridge_reference/AthenaSDK.java / AthenaConfig.java
 *
 * TODO(接入前必须提供)：ATHENA_TYPE(track_type, BM=5943) / REFERRER_APP_ID(BM=4987) /
 *   若走正式 appKey 则把 AthenaAnalytics.S(context, appKey, ...) 的空串换成真实值。
 */
public class HisavanaAnalyticsFeature implements IAnalyticsFeature {

    private static final String TAG = "WjAthenaAnalytics";
    private static final int ATHENA_TYPE = 5943;        // REPLACE_ME：传音后台分配的 track_type
    private static final int REFERRER_APP_ID = 4987;    // REPLACE_ME：referrer appId
    private static final String APP_KEY = "";           // REPLACE_ME：正式 appKey（留空走默认灰度通道）
    private static final String EVENT_NAME = "Drift_Sand";

    private final Context context;
    private String currentEvent;

    public HisavanaAnalyticsFeature(Context context) {
        this.context = context;
    }

    @Override public void analyticsOnStart() {
        try {
            AthenaAnalytics.e0(1);
            AthenaAnalytics.S(context, APP_KEY, ATHENA_TYPE, false, true);
            AthenaAnalytics.d0(false);
            AthenaAnalytics.c0(false);
            AthenaAnalytics.a0(REFERRER_APP_ID);
        } catch (Throwable t) {
            Log.e(TAG, "Athena init failed", t);
        }
    }

    @Override public void analyticsOnStop() { }

    @Override public void analyticsLogEvent(String name, boolean flag) {
        track(name, null);
    }

    @Override public void analyticsLogEvent(String name, Map<String, Object> params, boolean flag) {
        currentEvent = name;
        Bundle bundle = baseBundle(name);
        if (params != null) {
            for (Map.Entry<String, Object> e : params.entrySet()) {
                bundle.putString(e.getKey(), String.valueOf(e.getValue()));
            }
        }
        post(bundle);
    }

    /** 游戏侧用 begin/add/end 三段式记录时长事件。 */
    @Override public void analyticsBeginEvent() { }

    @Override public void analyticsAddEventParam(String key, String value) {
        currentEvent = key;   // 契约只给 key/value，按需缓存最近一次参数
    }

    @Override public void analyticsEndTimedEvent(String name) {
        if (currentEvent != null) { track(name, null); }
        currentEvent = null;
    }

    // ---------------- 内部 ----------------

    private Bundle baseBundle(String name) {
        Bundle bundle = new Bundle();
        bundle.putString("custom_track_name", name);        // 字段名以 AthenaConfig 为准，接入时对齐
        bundle.putString("ext", hostExt());
        return bundle;
    }

    private String hostExt() {
        try {
            JSONObject json = new JSONObject();
            json.put("host_pkg", context.getPackageName());
            json.put("host_vn", "REPLACE_ME");             // 采用 PackageManager 读取真实版本
            json.put("host_vc", "0");
            return json.toString();
        } catch (Exception e) {
            return "{}";
        }
    }

    private void post(Bundle bundle) {
        try {
            bundle.putString("vaid", AthenaAnalytics.K(AthenaAnalytics.M(), true));
            new U0.a(EVENT_NAME, ATHENA_TYPE).c(bundle, null).b();
        } catch (Throwable t) {
            Log.e(TAG, "athena track failed", t);
        }
    }

    private void track(String name, Map<String, Object> params) {
        analyticsLogEvent(name, params, false);
    }
}
