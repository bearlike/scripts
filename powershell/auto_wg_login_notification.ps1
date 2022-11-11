# Connect to WireGuard Tunnel when not connected to home network and sends login notification
$home_network = "Home Network"
$wireguard_network = "WG Network"

# Using BSSID might be a better way that using SSID but this works enough for me. 
$networks = (get-netconnectionProfile).Name

if (($home_network -In $networks) -and ($wireguard_network -In $networks)) {
    # Disconnect Wireguard, because there's no necessity for it
    Start-Process 'C:\Program Files\WireGuard\wireguard.exe' -ArgumentList '/uninstalltunnelservice', $wireguard_network + ".conf" -Wait -NoNewWindow -PassThru | Out-Null
}

elseif (($home_network -NotIn $networks) -and ($wireguard_network -NotIn $networks)) {
    # If Wireguard is connected or if I'm connected to my home network
    Start-Process 'C:\Program Files\WireGuard\wireguard.exe' -ArgumentList '/installtunnelservice', "C:\Files\configs\" + $wireguard_network + ".conf" -Wait -NoNewWindow -PassThru | Out-Null
}

# Send login notification via Gotify
Start-Process "C:\Program Files\Python310\python.exe" -ArgumentList "%PROJECTS%\Automations\Scripts\python\login_notification.py" -Wait -NoNewWindow -PassThru | Out-Null
