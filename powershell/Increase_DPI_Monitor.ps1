# Change DPI and Open-Shell Start Menu Orb size depending upon where you are sitting.
# <https://github.com/bearlike>
# Usage ./Increase_DPI_Monitor.ps1 -mode [table|bed]

param($mode="table")
$activeMonitorsRegPath = "HKCU:\Control Panel\Desktop\PerMonitorSettings\GSM5B95201NTPCPE984_01_07E6_D5^C875D5DD84C8C1D0473327B297D3BBAA"
$startOrbSizeRegPath = "HKCU:\Software\OpenShell\StartMenu\Settings"

if ($mode -eq "table") {
    # DpiValue = 1 when you're in front of monitor
    Write-Output "You're in front of the monitor."
    Write-Output "Increasing DPI and decreasing orb size."
    Set-ItemProperty -Path $activeMonitorsRegPath -Name 'DpiValue' -Value 1 -Force
    Set-ItemProperty -Path $startOrbSizeRegPath -Name 'StartButtonSize' -Value 85 -Force
}

elseif ($mode -eq "bed") {
    # DpiValue = 3 when you're on the bed
    Write-Output "You're on the bed."
    Write-Output "Decreasing DPI and increasing orb size."
    Set-ItemProperty -Path $activeMonitorsRegPath -Name 'DpiValue' -Value 3 -Force
    Set-ItemProperty -Path $startOrbSizeRegPath -Name 'StartButtonSize' -Value 120 -Force
}

else {
    Write-Output "Invalid input."
    Exit
}

# Logout if succesfilly changed registry
shutdown /L