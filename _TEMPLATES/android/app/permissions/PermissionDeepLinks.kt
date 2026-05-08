// =============================================================================
// PermissionDeepLinks.kt — REUSABLE TEMPLATE
// =============================================================================
//
// Reusable per orice Android app (SunriseApp, GemmaApp, viitoare).
// Sursa originală: GemmaApp v4.3.8 (2026-04-19).
//
// ## Cum folosesc în proiect nou:
// 1. Copiază acest fișier în `app/src/main/java/<package>/permissions/PermissionDeepLinks.kt`
// 2. Schimbă `package com.example.template.permissions` cu packagename-ul tău
// 3. (Opțional) Șterge Timber dacă proiectul folosește android.util.Log
// 4. Apelează: `PermissionDeepLinks.openBatteryOptimization(context)` din orice Activity/Composable
//
// ## Ce face:
// Deep-link DIRECT la pagina de toggle/approve pentru fiecare permisiune — user-ul nu
// mai rămâne în Settings-general, ci sare direct pe butonul unde trebuie să apese.
//
// Pe Vivo OriginOS/iQoo + alte OEM (Xiaomi MIUI, Oppo ColorOS, OnePlus, Huawei, Samsung),
// `openVivoAutoStart()` încearcă ComponentName-uri specifice pt pagina AutoStart whitelist.
//
// Toate metodele sunt fail-soft: fallback în cascadă la `ACTION_APPLICATION_DETAILS_SETTINGS`.
//
// ## Metode disponibile:
// - openBatteryOptimization()         — popup "Allow to ignore battery optimizations"
// - openAccessibilitySettings()       — lista Accessibility services
// - openNotificationListenerSettings()— toggle "Notification access"
// - openNotificationSettings()        — notification channels pt app (SDK 26+)
// - openUsageAccess()                 — toggle Usage Stats per app
// - openOverlayPermission()           — toggle "Display over other apps"
// - openInstallUnknownSources()       — toggle "Install unknown apps" (SDK 26+)
// - openVivoAutoStart()               — AutoStart whitelist (Vivo/iQoo + 5 OEM fallbacks)
// - openAppDetails()                  — fallback universal la App Info
// =============================================================================

package com.example.template.permissions

import android.content.ActivityNotFoundException
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.util.Log

object PermissionDeepLinks {

    private const val TAG = "PermissionDeepLinks"

    /** Request ignore battery opt — deschide direct popup-ul sistem "Allow". */
    fun openBatteryOptimization(context: Context) {
        val pkg = context.packageName
        val direct = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            .setData(Uri.parse("package:$pkg"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, direct) {
            val list = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            safeStart(context, list) { openAppDetails(context) }
        }
    }

    /** Accessibility list — deschide setările unde user apasă toggle pe app service. */
    fun openAccessibilitySettings(context: Context) {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /** Notification listener — pagina cu toggle pentru "Allow notification access". */
    fun openNotificationListenerSettings(context: Context) {
        val intent = Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS")
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /** POST_NOTIFICATIONS (SDK 33+) — pagina de notification channel al app-ului. */
    fun openNotificationSettings(context: Context) {
        val pkg = context.packageName
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, pkg)
        } else {
            appDetailsIntent(pkg)
        }.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /** Usage access (PACKAGE_USAGE_STATS) — pagina cu toggle per app. */
    fun openUsageAccess(context: Context) {
        val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /** Overlay SYSTEM_ALERT_WINDOW — toggle directly on app. */
    fun openOverlayPermission(context: Context) {
        val pkg = context.packageName
        val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
            .setData(Uri.parse("package:$pkg"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /** Unknown sources install — pentru a instala APK-uri prin app (per-app toggle SDK 26+). */
    fun openInstallUnknownSources(context: Context) {
        val pkg = context.packageName
        val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES)
                .setData(Uri.parse("package:$pkg"))
        } else {
            Intent(Settings.ACTION_SECURITY_SETTINGS)
        }.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        safeStart(context, intent) { openAppDetails(context) }
    }

    /**
     * Vivo iManager — pagină-listă cu TOATE permisiunile speciale ale app-ului (AutoStart,
     * Background Popup, Lockscreen Display etc. grupate într-un singur ecran). Preferă această
     * metodă în loc de `openVivoAutoStart` — user-ul vede contextul + toate toggle-urile, nu
     * doar unul izolat (care confuză user-ul dacă deja e activ).
     */
    fun openVivoAppPermissions(context: Context) {
        val pkg = context.packageName
        val candidates = listOf(
            ComponentName("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.PurviewTabActivity") to true,
            ComponentName("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.SoftwareManagerActivity") to false,
            ComponentName("com.iqoo.secure", "com.iqoo.secure.MainActivity") to false,
        )
        for ((cn, wantPkgExtra) in candidates) {
            val intent = Intent().setComponent(cn).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            if (wantPkgExtra) intent.putExtra("packagename", pkg)
            try { context.startActivity(intent); return } catch (_: Throwable) { /* try next */ }
        }
        openAppDetails(context)
    }

    /**
     * **DEPRECATED în favoarea [openVivoAppPermissions].** Direct-toggle deep-link este
     * confuz (user nu vede dacă e deja activ). Păstrat doar pt OEM-uri non-Vivo (fallback chain).
     */
    @Deprecated(
        "Folosește openVivoAppPermissions() — direct-toggle ascunde contextul.",
        ReplaceWith("openVivoAppPermissions(context)")
    )
    fun openVivoAutoStart(context: Context) {
        // Preferă pagini-listă, NU butonul direct
        val vivoCandidates = listOf(
            ComponentName("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.PurviewTabActivity"),
            ComponentName("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"),
            ComponentName("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"),
            ComponentName("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity"),
        )
        for (cn in vivoCandidates) {
            val intent = Intent().setComponent(cn).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            try { context.startActivity(intent); return } catch (_: Throwable) { /* try next */ }
        }
        // Other OEM fallbacks
        val oemFallbacks = listOf(
            ComponentName("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
            ComponentName("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"),
            ComponentName("com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity"),
            ComponentName("com.oneplus.security", "com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity"),
            ComponentName("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
            ComponentName("com.samsung.android.lool", "com.samsung.android.sm.ui.battery.BatteryActivity"),
        )
        for (cn in oemFallbacks) {
            val intent = Intent().setComponent(cn).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            try { context.startActivity(intent); return } catch (_: Throwable) { /* try next */ }
        }
        openAppDetails(context)
    }

    /** App details — toate toggle-urile de permisiuni within app info. Fallback universal. */
    fun openAppDetails(context: Context) {
        val intent = appDetailsIntent(context.packageName)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try {
            context.startActivity(intent)
        } catch (t: Throwable) {
            Log.w(TAG, "openAppDetails failed: ${t.message}")
        }
    }

    private fun appDetailsIntent(pkg: String): Intent =
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            .setData(Uri.parse("package:$pkg"))

    private fun safeStart(context: Context, intent: Intent, fallback: () -> Unit) {
        try {
            context.startActivity(intent)
        } catch (_: ActivityNotFoundException) {
            Log.w(TAG, "Intent not resolvable: ${intent.action}, falling back")
            fallback()
        } catch (t: Throwable) {
            Log.w(TAG, "Intent start failed: ${intent.action}: ${t.message}")
            fallback()
        }
    }
}
