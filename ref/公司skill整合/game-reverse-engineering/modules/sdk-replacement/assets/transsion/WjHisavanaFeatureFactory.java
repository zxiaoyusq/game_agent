package com.kumobius.android.features;

import android.app.Activity;

/**
 * 工厂替身：把 KumoAppActivity 的 IFeatureFactory 指向传音实现。
 * 契约：com.kumobius.android.features.IFeatureFactory#create(KumoAppActivity)
 *
 * 注意：KumoAppBase.setAdsFeatureFactory / setAnalyticsFeatureFactory 是**包内可见**静态方法，
 *      因此安装类必须落在 com.kumobius.android 包（见 WjSdkInstaller）。
 */
public final class WjHisavanaFeatureFactory implements IFeatureFactory {

    public static final int KIND_ADS = 1;
    public static final int KIND_ANALYTICS = 2;

    private final int kind;

    public WjHisavanaFeatureFactory(int kind) {
        this.kind = kind;
    }

    @Override public Object create(KumoAppActivity activity) {
        if (kind == KIND_ADS) {
            return new HisavanaAdsFeature(activity);
        }
        return new HisavanaAnalyticsFeature(activity.getApplicationContext() == null
                ? activity : activity.getApplicationContext());
    }
}
