<#
.SYNOPSIS
    Hermes PS Bridge — PowerShell interface for Windows system patching
.DESCRIPTION
    Runs on Windows via Task Scheduler or manual invocation.
    Reports system state back to Hermes via shared state file on D:\.
    
    Usage:
      powershell -ExecutionPolicy Bypass -File hermes-ps-bridge.ps1 -Check
      powershell -ExecutionPolicy Bypass -File hermes-ps-bridge.ps1 -Heal
      powershell -ExecutionPolicy Bypass -File hermes-ps-bridge.ps1 -Patch
.PARAMETER Check
    Report Windows system health (services, disk, updates, defender)
.PARAMETER Heal
    Fix common issues (restart services, clear temp, SFC scan)
.PARAMETER Patch
    Install pending Windows Updates (if available)
#>

param(
    [switch]$Check,
    [switch]$Heal,
    [switch]$Patch
)

$STATE_DIR = "D:\Hermes\State"
$REPORT_FILE = "$STATE_DIR\windows_report.json"
$TIMESTAMP = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
$D_DRIVE = "D:\"

if (-not (Test-Path $STATE_DIR)) {
    New-Item -ItemType Directory -Path $STATE_DIR -Force | Out-Null
}

function Write-Log {
    param($Message, $Level = "INFO")
    $entry = @{
        ts = $TIMESTAMP
        level = $Level
        module = "hermes-ps-bridge"
        message = $Message
    }
    Write-Output ($entry | ConvertTo-Json -Compress)
}

function Get-SystemHealth {
    Write-Log "Collecting Windows system health..."

    $os = Get-CimInstance Win32_OperatingSystem
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    $diskD = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'"
    $services = Get-Service | Where-Object { $_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic' }
    $updates = Get-WindowsUpdate -IsInstalled 0 -ErrorAction SilentlyContinue | Select-Object -First 10
    $defender = Get-MpComputerStatus
    $tasks = Get-ScheduledTask | Where-Object { $_.State -ne 'Ready' }

    $report = @{
        timestamp = $TIMESTAMP
        os = @{
            name = $os.Caption
            version = $os.Version
            build = $os.BuildNumber
            last_boot = $os.LastBootUpTime.ToString("yyyy-MM-dd HH:mm:ss")
            uptime_days = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalDays, 1)
        }
        c_drive = @{
            size_gb = [math]::Round($disk.Size / 1GB, 1)
            free_gb = [math]::Round($disk.FreeSpace / 1GB, 1)
            free_pct = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 0)
        }
        d_drive = @{}
        services_failed = @($services | ForEach-Object { $_.Name })
        pending_updates = @($updates | ForEach-Object { $_.Title })
        defender = @{
            realtime = $defender.RealTimeProtectionEnabled
            definitions = $defender.AntivirusSignatureVersion
            last_scan = $defender.QuickScanEndTime
        }
        tasks_failed = @($tasks | ForEach-Object { $_.TaskName })
    }

    if ($diskD) {
        $report.d_drive = @{
            size_gb = [math]::Round($diskD.Size / 1GB, 1)
            free_gb = [math]::Round($diskD.FreeSpace / 1GB, 1)
            free_pct = [math]::Round(($diskD.FreeSpace / $diskD.Size) * 100, 0)
        }
    }

    $report | ConvertTo-Json -Depth 5 | Out-File $REPORT_FILE -Encoding UTF8
    Write-Log "Report saved to $REPORT_FILE"
    return $report
}

function Invoke-Heal {
    Write-Log "=== Windows Heal Pass ==="

    $cleaned = 0
    $tempPaths = @("$env:TEMP", "$env:WINDIR\Temp", "$env:WINDIR\Prefetch")
    foreach ($p in $tempPaths) {
        if (Test-Path $p) {
            try {
                Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue |
                    Where-Object { -not $_.PSIsContainer } |
                    ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue; $cleaned++ }
            } catch {}
        }
    }
    Write-Log "Cleaned $cleaned temp files"

    Write-Log "Running SFC scan..."
    $sfc = Start-Process -FilePath "sfc" -ArgumentList "/scannow" -NoNewWindow -Wait -PassThru
    Write-Log "SFC exit code: $($sfc.ExitCode)"

    $stopped = @()
    $failed = Get-Service | Where-Object { $_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic' }
    foreach ($s in $failed) {
        try {
            Start-Service $s.Name -ErrorAction SilentlyContinue
            $stopped += $s.Name
        } catch {}
    }
    if ($stopped.Count -gt 0) {
        Write-Log "Restarted $($stopped.Count) services: $($stopped -join ', ')" "WARN"
    }

    return @{temp_cleaned = $cleaned; services_restarted = $stopped}
}

function Install-PendingUpdates {
    Write-Log "Checking for Windows Updates..."
    try {
        $updates = Get-WindowsUpdate -IsInstalled 0 -ErrorAction SilentlyContinue
        if ($updates) {
            Write-Log "$($updates.Count) updates pending, installing..." "WARN"
            Install-WindowsUpdate -AcceptAll -AutoReboot:$false -ErrorAction SilentlyContinue
        } else {
            Write-Log "No pending updates"
        }
    } catch {
        Write-Log "Update check failed: $_" "ERROR"
    }
}

switch ($true) {
    $Check {
        $report = Get-SystemHealth
        Write-Output ($report | ConvertTo-Json -Depth 5)
    }
    $Heal {
        $result = Invoke-Heal
        Write-Output ($result | ConvertTo-Json)
    }
    $Patch {
        Install-PendingUpdates
    }
    default {
        $report = Get-SystemHealth
        Write-Output ($report | ConvertTo-Json -Depth 5)
    }
}
