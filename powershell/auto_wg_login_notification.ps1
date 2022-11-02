# Connect to WireGuard Tunnel when not connected to home network and sends login notification

# Using BSSID might be a better way that using SSID but this works enough for me. 
if ((get-netconnectionProfile).Name -ne "Home_Network") {
    Start-Process 'C:\Program Files\WireGuard\wireguard.exe' -ArgumentList '/installtunnelservice', 'my-tunnel.conf' -Wait -NoNewWindow -PassThru | Out-Null
}
# Send login notification via Gotify
Start-Process "C:\Program Files\Python310\python.exe" -ArgumentList "Z:\path\to\login_notification.py" -Wait -NoNewWindow -PassThru | Out-Null