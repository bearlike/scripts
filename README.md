# Scripts
Collection of automation scripts. Use it if you have the same purpose.

Got scripts? See [Contributing](.github/CONTRIBUTING.md).
<br> Got Issues? See [Issues](https://github.com/bearlike/scripts/issues)

## Lot of Scripts

| **Title**                        | **Filename**                                                                       | **Type** | **Description**                                                                                                                       |
|----------------------------------|------------------------------------------------------------------------------------|----------|---------------------------------------------------------------------------------------------------------------------------------------|
| Clean System                     | [`clean-system.sh`](bash/clean-system.sh)                                          | Bash     | "Removing unused `apt` packages, kernels, thumbnail cache, and docker objects"                                                        |
| Cloudflare - Add DNS A record    | [`cloudflare_create_dns_record.py`](python/cloudflare_create_dns_record.py)        | Python   | Adds DNS A record pointing to a mentioned server using Cloudflare API v4.                                                             |
| Cloudflare - Delete DNS A record | [`cloudflare_delete_dns_records.py`](python/cloudflare_delete_dns_records.py)      | Python   | Deletes DNS A record pointing to a mentioned server using Cloudflare API v4.                                                          |
| Deletes old files in a directory | [`delete_old_file.py`](python/delete_old_file.py)                                  | Python   | Periodically deletes old files from a directory. For use in torrent box(es)                                                           |
| Find and Fix Git Email Leak      | [`find-fix-git-email-leak/`](https://github.com/bearlike/find-fix-git-email-leak/) | Python   | Find and Fix publicly accessible commit email addresses.                                                                              |
| Macro Keyboard                   | [`Lua Macros/marco_keyboard.lua`](lua/Lua%20Macros/marco_keyboard.lua)               | Lua      | Load this script in [Lua Macros](https://github.com/me2d13/luamacros) to use multiple-keyboards for macro-triggerring application..   |
| Macro Keyboard Companion         | [`macro_keyboard_companion.py`](python/macro_keyboard_companion.py)                | Python   | Companion script for my Macro Keyboard. `Lua Macros/marco_keyboard.lua` for keyboard input grabbing. Basic alternative for AutoHotKey |
| Nextcloud Snapshot               | [`nextcloud_snapshot.sh`](bash/nextcloud_snapshot.sh)                              | Bash     | Snapshot Nextcloud and uploads to remote locations such as Google Drive. Can be used as a Cronjob                                     |
| Raspberry Pi MOTD                | [`status_motd_rpi.sh`](bash/status_motd_rpi.sh)                                    | Bash     | Raspberry Pi MOTD that displays basic system information on login                                                                     |
| Turn off Samsung TV              | [`tv-shutdown.py`](python/tv-shutdown.py)                                          | Python   | Turn off Samsung TV using `samsungctl`                                                                                                |
| Update System                    | [`update-system.sh`](bash/update-system.sh)                                        | Bash     | For Updating `apt` Packages and Portainer via docker                                                                                  |


**[`^        back to top        ^`](#Scripts)**


## License
[![Creative Commons License](http://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)
<br> This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).
