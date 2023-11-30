# Toggle TV via Home Assistant when HDMI is connected

<#
    This script will check the monitor's connection status, compare it with the 
        stored state in a dotfile, and update the file accordingly. 
    If there's a change in the state, it will execute the API request to HA.

    Schedule a task with the below event triggers:
    - Microsoft-Windows-DeviceSetupManager/Admin::112 - HDMI connected (Accurate)
    - Microsoft-Windows-Kernel-PnP/Device Management::1010  - May track disconnected devices
    Make sure to set the task to run with highest privileges and to run
                                        whether user is logged on or not.
    Also, set the task to queue a new instance if the task is already running.

    If you want to silently run the script, use the silent_spawn.vbs 
                script to run this script.

    Optional: Pass the -must_toggle (-must_toggle $true) flag to force
                the script to toggle the TV. 
            Useful to turn off the TV during Workstation Lock.
#>

# Note:
# `Install-Module -Name BurntToast -Force` as admin to install BurntToast module

# TODO: Restrict to home networks only (Maybe use IP address or Wi_Fi SSID(s) to check)
# TODO: Check if monitor is in use (i.e., if extended or duplicated to the display).

# Parse command-line arguments
param (
    [string]$must_toggle = "false",
    [string]$HA_TOKEN = "NONE"
)

# Convert string to boolean
$must_toggle_bool = $false
if ($must_toggle -eq "true") {
    $must_toggle_bool = $true
}

# Global Variables
# Use HA_TOKEN environment variable if HA_TOKEN param is not set
if ($HA_TOKEN -eq "NONE") {
    $HA_TOKEN = [System.Environment]::GetEnvironmentVariable("HA_TOKEN", "Machine")
}

$NCPATH = "D:\Users\Krishna_Alagiri\Nextcloud"
$MonitorID = "PRI0033"
$URL = "http://192.168.1.206:8123/api/services/scene/turn_on"
$Data = '{"entity_id": "scene.tv_power"}'
$Headers = @{
    "Authorization" = "Bearer $HA_TOKEN"
    "Content-Type"  = "application/json"
}
# ! TODO: Possible error for Workstation Lock
$stateFile = "C:\Files\logs\.monitorState"
$bootStateFile = "C:\Files\logs\.LastBootState"
$logFile = "C:\Files\logs\monitor.log"

# Print generic banner
# Get-Content -Path "$NCPATH\Documents\Config\kkbot_banner.txt"

# Create log file if it doesn't exist
if (-Not (Test-Path $logFile)) {
    New-Item -Path $logFile -ItemType File
}

# Function to log messages
function Set-Log-Message($message) {
    Add-Content $logFile -Value ("[" + (Get-Date) + "] " + $message)
}


# Exit if HA_TOKEN is not set
if ($HA_TOKEN -eq $null) {
    Set-Log-Message "HA_TOKEN not set. Exiting."
    exit
}


# Function to check for monitor
function Get-MonitorStatus {
    $monitors = Get-WmiObject WmiMonitorID -Namespace root\wmi
    foreach ($monitor in $monitors) {
        $id = $monitor.InstanceName.ToString()
        if ($id.Contains($MonitorID)) {
            Set-Log-Message "Found Desired Monitor ID = ($id)"
            return $true
        }
    }
    Set-Log-Message "Desired monitor not found"
    return $false
}

# Function to send API request to Home Assistant
function Send-HARequest {
    # Sleep for 3 seconds to allow monitor to turn on/off
    Start-Sleep -Seconds 3
    Invoke-RestMethod -Uri $URL -Method Post -Headers $Headers -Body $Data
    Set-Log-Message "Sent API request to Home Assistant"
}

# Function to create and display a toast notification
function Show-Notification($currentState) {
    if ($currentState) {
        $message = "Turning on Dynex TV since HDMI is connected"
    }
    else {
        $message = "Turning off Dynex TV since HDMI is disconnected"
    }
    $title = "Monitor State Changed"
    $iconPath = "$NCPATH\Documents\Config\.icons\KK.png" # Ensure this path is correct

    # Ensure BurntToast module is loaded
    if (-not (Get-Module -ListAvailable -Name BurntToast)) {
        Install-Module -Name BurntToast -Force
    }
    Import-Module BurntToast

    # Create Toast Notification
    New-BurntToastNotification -Text $title, $message -AppLogo $iconPath -Sound "Default" -ExpirationTime (Get-Date).AddSeconds($timeout)
    Set-Log-Message $message
}

function Update-MonitorStatus($currentState) {
    # Store monitor state to a file
    $currentState | Out-File $stateFile
    Set-Log-Message "State changed. Updated state file with: $currentState"
    Send-HARequest
    Show-Notification -currentState $currentState
    exit
}


function Get-IsCurrentBoot {
    # Get the last boot up time using WMIC and store it in a variable
    $currentBootState = (wmic os get lastbootuptime | Out-String).Trim() -split "\r?\n" | Where-Object { $_ -match "\d+" } | Select-Object -First 1
    if (-Not (Test-Path $logFile)) {
        Set-Log-Message "Last boot file not found. Removing monitor state."
        $lastBootState = $currentBootState
        Remove-Item $stateFile
    }
    else {
        $lastBootState = Get-Content -Path $bootStateFile
        Set-Log-Message "Last boot file found. Using Last boot state: $lastBootState"
    }
    if ($lastBootState -ne $currentBootState) {       
        Set-Log-Message "Change in boot state. Deleting monitor state."
        # Remove if exist
        if (Test-Path $stateFile) {
            Remove-Item $stateFile
        }
    }
    # Write the current boot state to the file
    Set-Content -Path $bootStateFile -Value $currentBootState
}


# Driver Logic
Set-Log-Message "==================== Starting script ===================="
Get-IsCurrentBoot
$lastState = $false
if (Test-Path $stateFile) {
    $lastState = [System.Convert]::ToBoolean((Get-Content $stateFile))
    Set-Log-Message "Loaded last state from file: $lastState"
}
# True if monitor is connected, False if disconnected
$currentState = Get-MonitorStatus

# Turn off TV even if connected to monitor
if ($currentState -and $must_toggle_bool) {
    # TODO: Update notification message for this use case
    Update-MonitorStatus -currentState $currentState
}
# Turn off TV if monitor is disconnected and Turn on TV if monitor is connected
if ($currentState -ne $lastState) {
    Update-MonitorStatus -currentState $currentState
}
# Will only reach here if there's no change in monitor state
Set-Log-Message "No change in monitor state."

