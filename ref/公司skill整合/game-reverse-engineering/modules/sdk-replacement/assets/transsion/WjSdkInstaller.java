package com.kumobius.android;   // 必须与本包一致：KumoAppBase.setXxxFeatureFactory 为包内可见

import com.kumobius.android.features.WjHisavanaFeatureFactory;

/**
 * 装配入口：在 KumoAppBase.onCreate() 装完默认工厂之后调用，覆盖为传音实现。
 *
 * 注入方式（二选一，推荐 A）：
 *   A. patch KumoAppBase.onCreate()，在 return-void 之前插入：
 *        invoke-static {p0}, Lcom/kumobius/android/WjSdkInstaller;->install(Landroid/content/Context;)V
 *   B. 新增 ContentProvider（WjSdkInitProvider）在 onCreate 中调用：
 *        KumoAppBase.getAdsFeatureFactory();   // 先触发目标类加载，避免 <clinit> 覆盖
 *        WjSdkInstaller.install(getContext());
 *
 * 注意顺序：install() 必须在 KumoAppBase.onCreate() 之后执行，否则会被默认工厂覆盖。
 */
public final class WjSdkInstaller {

    private WjSdkInstaller() { }

    public static void install(android.content.Context context) {
        KumoAppBase.setAdsFeatureFactory(new WjHisavanaFeatureFactory(WjHisavanaFeatureFactory.KIND_ADS));
        KumoAppBase.setAnalyticsFeatureFactory(new WjHisavanaFeatureFactory(WjHisavanaFeatureFactory.KIND_ANALYTICS));
        // 如需保留 Google Play 游戏服务（榜/成就）与 IAP，不动 IapFeatureFactory / AchievementsFeatureFactory。
    }
}
