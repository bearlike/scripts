# Connect to WireGuard Tunnel when not connected to home network and sends login notification
$home_network = "Home Network"
$wireguard_network = "WG Network"

# Using BSSID might be a better way that using SSID but this works enough for me. 
$networks = (get-netconnectionProfile).Name

if (($home_network -In $networks) -and ($wireguard_network -In $networks)) {
    Start-Process 'C:\Program Files\WireGuard\wireguard.exe' -ArgumentList '/uninstalltunnelservice', "$wireguard_network" -Wait -NoNewWindow -PassThru | Out-Null
    # As a fallback, a dialog ballon is thrown
    [reflection.assembly]::loadwithpartialname('System.Windows.Forms')
    [reflection.assembly]::loadwithpartialname('System.Drawing')
    $notify = new-object system.windows.forms.notifyicon
    $notify.icon = [System.Drawing.SystemIcons]::Information
    $notify.visible = $true
    $notify.showballoontip(10, 'Disconnected from $wireguard_network tunnel', "Disconnected from the Wireguard tunnel since it was connected to both the home network and tunnel.", [system.windows.forms.tooltipicon]::None)
}

elseif (($home_network -NotIn $networks) -and ($wireguard_network -NotIn $networks)) {
    # If Wireguard is connected or if I'm connected to my home network
    Start-Process 'C:\Program Files\WireGuard\wireguard.exe' -ArgumentList '/installtunnelservice', "C:\Files\configs\$wireguard_network.conf" -Wait -NoNewWindow -PassThru | Out-Null
}

# Send login notification via Gotify
Start-Process "C:\Program Files\Python311\python.exe" -ArgumentList "$Env:PROJECTS\Automations\Scripts\python\login_notification.py" -Wait -NoNewWindow -PassThru | Out-Null