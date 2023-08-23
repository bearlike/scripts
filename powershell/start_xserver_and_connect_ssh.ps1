# Sets an env variable and SSH into Hurricane with X11 forwarding enabled.

# Hi-DPI settings:
# Choose Properties > Compatibility tab > Change high DPI settings > 
#    Enable Override high DPI scaling > change to 'Application' 
#    Do this for xlaunch.exe, vcxsrv.exe and Xming.exe 

# Set environment variable
$env:DISPLAY = "127.0.0.1:0.0"

# Variable to decide X servers
$XServer = "VcXsrv" # Xming or VcXsrv
echo "Starting $XServer X server..."

# Kill any active Xming or VcXsrv processes
Get-Process | Where-Object { $_.Path -like "C:\Program Files (x86)\Xming\Xming.exe" -or $_.Path -like "C:\Program Files\VcXsrv\vcxsrv.exe" } | Stop-Process -Force

# Conditionally start the X server based on the variable
if ($XServer -eq "Xming") {
    Start-Process -FilePath "C:\Program Files (x86)\Xming\Xming.exe" -ArgumentList ":0 -clipboard -multiwindow -dpi 120"
}
elseif ($XServer -eq "VcXsrv") {
    Start-Process -FilePath "C:\Program Files\VcXsrv\vcxsrv.exe" -ArgumentList ":0 -clipboard -multiwindow -wgl -dpi 120 -screen 0 2560x1440 -ac"
}

# SSH into the server with the specified options
ssh -c chacha20-poly1305@openssh.com -Y test_user@192.168.1.420 -p 22

# Once the SSH is closed, close all the X server processes
Get-Process | Where-Object { $_.Path -like "C:\Program Files (x86)\Xming\Xming.exe" -or $_.Path -like "C:\Program Files\VcXsrv\vcxsrv.exe" } | Stop-Process -Force
echo "X server processes killed."