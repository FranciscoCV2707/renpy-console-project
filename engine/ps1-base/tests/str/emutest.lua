-- Captura del video STR de prueba: una captura cada 2 s de juego y salida.
local frames = 0
local shots = {300, 600, 900, 1200}
local outdir = 'E:/Dev/vn-engine-ps1/build/str/shots'
local done = {}
STRTEST_LISTENER = PCSX.Events.createEventListener('GPU::Vsync', function()
  frames = frames + 1
  for _, f in ipairs(shots) do
    if frames == f and not done[f] then
      done[f] = true
      local shot = PCSX.GPU.takeScreenShot()
      local file = Support.File.open(outdir .. '/f' .. f .. '.raw', 'TRUNCATE')
      file:writeMoveSlice(shot.data)
      file:close()
      local log = Support.File.open(outdir .. '/shots.txt', 'APPEND')
      log:write('f' .. f .. ' ' .. shot.width .. ' ' .. shot.height .. '\n')
      log:close()
    end
  end
  if frames > 1300 then
    PCSX.quit(0)
  end
end)
