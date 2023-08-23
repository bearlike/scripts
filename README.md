<!-- Generated on 2023-08-23 20:22:57+00:00  -->

<!-- Do not edit this file. Edit README.md/base.md.j2 instead. -->
# Scripts
Collection of automation scripts. Use it if you have the same purpose.

[![CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-brightgreen)](license.md)
[![DeepSource](https://deepsource.io/gh/bearlike/scripts.svg/)](https://deepsource.io/gh/bearlike/scripts/)

Got scripts? See [Contributing](.github/CONTRIBUTING.md).
<br> Got Issues? See [Issues](https://github.com/bearlike/scripts/issues)

## Lot of Scripts

|               Title                |                                                Filename                                                |       Type       |                                                                                              Description                                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Fancy MOTD                         | [`fancy_motd.sh`](bash/fancy_motd.sh)                                                                  | Bash             | A really cool MOTD that displays system information on login. [**`Screenshot 🖼️`**](https://i.imgur.com/GibVoZM.jpg)                                                                                   |
| Raspberry Pi MOTD                  | [`status_motd_rpi.sh`](bash/status_motd_rpi.sh)                                                        | Bash             | Raspberry Pi MOTD that displays basic system information on login. [**`Screenshot 🖼️`**](https://i.imgur.com/jlRtMrF.jpg)                                                                              |
| Nextcloud Snapshot                 | [`nextcloud_snapshot.sh`](bash/nextcloud_snapshot.sh)                                                  | Bash             | Snapshot Nextcloud and uploads to remote locations such as Google Drive. Can be used as a Cronjob.                                                                                                     |
| Clean System                       | [`clean-system.sh`](bash/clean-system.sh)                                                              | Bash             | Removing unused `apt` packages, kernels, thumbnail cache, and docker objects.                                                                                                                          |
| Update System                      | [`update-system.sh`](bash/update-system.sh)                                                            | Bash             | For Updating `apt` Packages and Portainer via docker.                                                                                                                                                  |
| Alias and functions                | [`alias.sh`](bash/alias.sh)                                                                            | Bash             | Human friendly aliases and functions                                                                                                                                                                   |
| Send notificatiovs via gotify      | [`gotify-send.sh`](bash/gotify-send.sh)                                                                | Bash             | Send notifications via gotify                                                                                                                                                                          |
| Measure Voltage RPi                | [`measure_volts_rpi.sh`](bash/measure_volts_rpi.sh)                                                    | Bash             | Display Raspberry Pi voltage and checks if it is undervolted.                                                                                                                                          |
| Scan Pages                         | [`scan_page.sh`](bash/scan_page.sh)                                                                    | Bash             | Scan a page from my HP flatbed scanner through SANE (Scanner Access Now Easy) interface                                                                                                                |
| Gotify Docker Stack                | [`gotify/docker-compose.yml`](/docker-compose/gotify/docker-compose.yml)                               | docker-compose   | Basic Gotify Docker stack. [Refer documentation](https://gotify.net/docs/)                                                                                                                             |
| Homeassistant Docker Stack         | [`homeassistant/docker-compose.yml`](/docker-compose/homeassistant/docker-compose.yml)                 | docker-compose   | Home Assistant stack with healthcheck & support for accessing host docker containers. [`configuration.yaml`](/docker-compose/homeassistant/configuration.yaml) with some custom sensors (VPN IP, etc.) |
| Local Sites Docker Stack           | [`local_sites/docker-compose.yml`](/docker-compose/local_sites/docker-compose.yml)                     | docker-compose   | Docker stack to host static site(s)                                                                                                                                                                    |
| MongoDB Docker Stack               | [`mongodb/docker-compose.yml`](/docker-compose/mongodb/docker-compose.yml)                             | docker-compose   | MongoDB and Mongo Express                                                                                                                                                                              |
| Nextcloud Docker Stack             | [`nextcloud/docker-compose.yml`](/docker-compose/nextcloud/docker-compose.yml)                         | docker-compose   | The Nextcloud Docker stack that I use.                                                                                                                                                                 |
| NGINX Proxy Manager Docker Stack   | [`nginx_proxy_manager/docker-compose.yml`](/docker-compose/nginx_proxy_manager/docker-compose.yml)     | docker-compose   | Simple NGINX Proxy Manager Docker Stack                                                                                                                                                                |
| Pi-Hole Docker Stack               | [`pihole/docker-compose.yml`](/docker-compose/pihole/docker-compose.yml)                               | docker-compose   | Simple Pi-Hole Docker Stack                                                                                                                                                                            |
| ScanservJS Docker Stack            | [`scanner_app/docker-compose.yml`](/docker-compose/scanner_app/docker-compose.yml)                     | docker-compose   | SANE web UI frontend for scanners.                                                                                                                                                                     |
| Secrets Manager Docker Stack       | [`simple_secret_manager/docker-compose.yml`](/docker-compose/simple_secret_manager/docker-compose.yml) | docker-compose   | Secure storage, and delivery for tokens Visit [bearlike/simple-secrets-manager](https://github.com/bearlike/simple-secrets-manager) to know more.                                                      |
| Watchtower Docker Stack            | [`watchtower/docker-compose.yml`](/docker-compose/watchtower/docker-compose.yml)                       | docker-compose   | Simple Watchtower Docker Stack                                                                                                                                                                         |
| Gluetun + qBittorrent Docker Stack | [`qbitorrent+gluetun/docker-compose.yml`](/docker-compose/qbitorrent%2Bgluetun/docker-compose.yml)     | docker-compose   | qBittorrent with all connection routed through a Gluetun container (VPN). Purely for educational purpose                                                                                               |
| Gluetun + qBittorrent Docker Stack | [`qbitorrent+tor/docker-compose.yml`](/docker-compose/qbitorrent%2Btor/docker-compose.yml)             | docker-compose   | qBittorrent with all connection routed through the Tor network (via SOCKS5). Not recommended (See why on the inline comments). Purely for educational purpose                                          |
| Wireguard Docker Stack             | [`wireguard/docker-compose.yml`](/docker-compose/wireguard/docker-compose.yml)                         | docker-compose   | Simple Wireguard Docker Stack                                                                                                                                                                          |
| Download Torrents on Colab         | [`notebooks/Ultra_Torrent_Downloader.ipynb`](/notebooks/Ultra_Torrent_Downloader.ipynb)                | Jupyter Notebook | Downloading Torrents using Google Colab. Powered by qBittorrent WebUI and ngrok.                                                                                                                       |
| Macro Keyboard                     | [`Lua Macros/marco_keyboard.lua`](lua/Lua%20Macros/marco_keyboard.lua)                                 | Lua              | Load this script in [Lua Macros](https://github.com/me2d13/luamacros) to use multiple-keyboards for macro-triggerring application.                                                                     |
| DPI Scaling                        | [`Increase_DPI_Monitor.ps1`](powershell/Increase_DPI_Monitor.ps1)                                      | Powershell       | Change DPI and Open-Shell Start Menu Orb size depending upon where you are sitting.                                                                                                                    |
| Auto WG and Login Notification     | [`auto_wg_login_notification.ps1`](powershell/auto_wg_login_notification.ps1)                          | Powershell       | Connect to WireGuard Tunnel when not connected to home network and sends login notification.                                                                                                           |
| Start X Server & SSH into a server | [`start_xserver_and_connect_ssh.ps1`](powershell/start_xserver_and_connect_ssh.ps1)                    | Powershell       | Start X Server on Windows (Xming or VcXsrv) and SSH into a server                                                                                                                                      |
| Cloudflare - Add DNS A record      | [`cloudflare_create_dns_record.py`](python/cloudflare_create_dns_record.py)                            | Python           | Adds DNS A record pointing to a mentioned server using Cloudflare API v4.                                                                                                                              |
| Cloudflare - Delete DNS A record   | [`cloudflare_delete_dns_records.py`](python/cloudflare_delete_dns_records.py)                          | Python           | Deletes DNS A record pointing to a mentioned server using Cloudflare API v4.                                                                                                                           |
| Deletes old files in a directory   | [`delete_old_file.py`](python/delete_old_file.py)                                                      | Python           | Periodically deletes old files from a directory. For use in torrent box(es).                                                                                                                           |
| Find and Fix Git Email Leak        | [`find-fix-git-email-leak/`](https://github.com/bearlike/find-fix-git-email-leak/)                     | Python           | Find and Fix publicly accessible commit email addresses.                                                                                                                                               |
| Macro Keyboard Companion           | [`macro_keyboard_companion.py`](python/macro_keyboard_companion.py)                                    | Python           | Companion script for my Macro Keyboard. `Lua Macros/marco_keyboard.lua` for keyboard input grabbing. Basic alternative for AutoHotKey.                                                                 |
| Turn off Samsung TV                | [`tv-shutdown.py`](python/tv-shutdown.py)                                                              | Python           | Turn off Samsung TV using `samsungctl`.                                                                                                                                                                |
| Login Notification via Gotify      | [`login_notification.py`](python/login_notification.py)                                                | Python           | Retrieves `Gotify` tokens from `Simple Secrets Manager (SSM)` and sends notification on user login. For Windows, Use task scheduler to automate.                                                       |


**[`^        back to top        ^`](#Scripts)**


## License
[![Creative Commons License](http://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)
<br> This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).