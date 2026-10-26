local ffi = require('ffi')
local mem = PCSX.getMemPtr()
local addr = 0x0143bc
local frames = 0
PLAYER_LISTENER = PCSX.Events.createEventListener('GPU::Vsync', function()
  frames = frames + 1
  if frames == 1800 then
    local v = {}
    for i = 0, 7 do v[#v+1] = tostring(ffi.cast('uint32_t*', mem + addr + 4*i)[0]) end
    local f = Support.File.open('E:/Dev/vn-engine-ps1/build/str/player/result.txt', 'TRUNCATE')
    f:write(table.concat(v, ' ') .. '\n'); f:close()
    PCSX.quit(0)
  end
end)


