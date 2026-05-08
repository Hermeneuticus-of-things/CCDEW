# PermissionDeepLinks Template

**Reusable per orice Android app.**

Sursa originală: Android permission deep-link template

## Instalare într-un proiect nou

1. Copiază `PermissionDeepLinks.kt` în `app/src/main/java/<your.package>/permissions/`
2. Schimbă `package com.example.template.permissions` → `package <your.package>.permissions`
3. Opțional: schimbă `android.util.Log` → `timber.log.Timber` dacă ai Timber
4. Apelează din Activity/Composable:
   ```kotlin
   PermissionDeepLinks.openBatteryOptimization(context)
   PermissionDeepLinks.openOverlayPermission(context)
   PermissionDeepLinks.openVivoAutoStart(context) // Vivo/Xiaomi/Oppo/OnePlus/Huawei/Samsung
   ```

## Ce face

Deep-link DIRECT la pagina exactă de toggle/approve pentru fiecare permisiune Android.
Fail-soft: fallback în cascadă la `ACTION_APPLICATION_DETAILS_SETTINGS`.

## Metode

| Metodă | Ce deschide |
|---|---|
| `openBatteryOptimization` | Popup sistem "Allow to ignore battery optimizations" |
| `openAccessibilitySettings` | Lista Accessibility services |
| `openNotificationListenerSettings` | Toggle "Notification access" |
| `openNotificationSettings` | Notification channels per app (SDK 26+) |
| `openUsageAccess` | Toggle Usage Stats per app |
| `openOverlayPermission` | Toggle "Display over other apps" |
| `openInstallUnknownSources` | Toggle "Install unknown apps" (SDK 26+) |
| `openVivoAutoStart` | AutoStart whitelist (Vivo/iQoo + 5 OEM fallbacks) |
| `openAppDetails` | Fallback universal la App Info |

## OEM-uri acoperite în `openVivoAutoStart`

- Vivo/iQoo (4 candidates)
- Xiaomi MIUI (`com.miui.securitycenter`)
- Oppo ColorOS (`com.coloros.safecenter`, `com.oppo.safe`)
- OnePlus OxygenOS (`com.oneplus.security`)
- Huawei EMUI (`com.huawei.systemmanager`)
- Samsung OneUI (`com.samsung.android.lool`)

## Exemplu integrare în Permission Wizard

```kotlin
Button(onClick = {
    if (Settings.canDrawOverlays(context)) {
        onNext()
    } else {
        PermissionDeepLinks.openOverlayPermission(context)
    }
}) { Text("Deschide toggle Overlay") }
```
