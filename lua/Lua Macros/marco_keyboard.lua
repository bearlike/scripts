-- For use with Lua Macros
--- assign logical name to macro keyboard
lmc_assign_keyboard('MACROS');

-- Application/Script variables --
local browser = "C:\\Users\\Admin\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
local win_run = "C:\\\\Scripts\\macro_keyboard_companion.py"

-- define callback for whole device
lmc_set_handler('MACROS',function(button, direction)
  if (direction == 1) then return end  -- ignore down
  if     (button == string.byte('X')) then lmc_spawn(browser, "https://mail.google.com/")
  elseif (button == string.byte('C')) then lmc_spawn(browser, "http://mydesk.morganstanley.com/")
  elseif (button == string.byte('M')) then lmc_spawn(browser, "https://calendar.google.com/")
  elseif (button == 188)              then lmc_spawn(browser, "http://torrent.home/")
  elseif (button == string.byte('P')) then lmc_spawn(browser, "http://portainer.home/")
  elseif (button == 190)              then lmc_spawn(browser, "https://nextcloud.home/apps/passwords")
  elseif (button == string.byte('Q')) then lmc_spawn("explorer.exe", "C:\\Users\\Admin\\Downloads")
  elseif (button == string.byte('W')) then lmc_spawn("explorer.exe", "C:\\Users\\Admin\\Documents")
  elseif (button == string.byte('N')) then lmc_spawn("python", win_run, "keebs", "snip")
  elseif (button == string.byte('T')) then lmc_spawn("python", win_run, "run", "taskmgr.exe")
  elseif (button == string.byte('A')) then lmc_spawn("python", win_run, "keebs", "vss_cmd_palette")
  elseif (button == 27)               then lmc_spawn("python", win_run, "off_tv")
  elseif (button == string.byte('V')) then lmc_spawn("C:\\Program Files (x86)\\Zoom\\bin\\Zoom.exe")
  elseif (button == string.byte('B')) then lmc_spawn("C:\\Users\\Admin\\AppData\\Local\\WhatsApp\\WhatsApp.exe")
  elseif (button == string.byte('Z')) then lmc_spawn("notepad")
  else print('Not yet assigned: ' .. button)
  end
end)
