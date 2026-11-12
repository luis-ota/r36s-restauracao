local t = 0

function love.update(dt)
  t = t + dt
  if t > 25 then
    love.event.quit()
  end
end

function love.joystickpressed(j, b)
  -- 12 = SELECT, 13 = START (mapeamento do joydev deste aparelho)
  if b == 12 or b == 13 then
    love.event.quit()
  end
end

function love.draw()
  love.graphics.clear(0.04, 0.04, 0.07)
  love.graphics.setColor(0.86, 0.10, 0.18)
  local x = 40 + (math.sin(t * 1.6) * 0.5 + 0.5) * (640 - 240)
  love.graphics.rectangle("fill", x, 190, 160, 90)
  love.graphics.setColor(0.95, 0.93, 0.85)
  love.graphics.print("LOVE 11.5 no R36S", 40, 36)
  love.graphics.print("fps: " .. love.timer.getFPS(), 40, 60)
  love.graphics.print("t = " .. string.format("%.1f", t), 40, 84)
  love.graphics.print("SELECT/START saem", 40, 440)
end
