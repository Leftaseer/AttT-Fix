-- AttTFix embedded script: runs right after GUIScenes.lua is loaded.
-- Uses C functions registered by dinput8.dll: AttTFix_Log, AttTFix_ModeCount, AttTFix_Mode,
-- AttTFix_Current, AttTFix_SetResolution.
local ok, err = pcall(function()
  AttTFix = AttTFix or {}
  local O = GUIScene and GUIScene.Options
  if not O then AttTFix_Log("GUIScene.Options not found yet") return end
  if O.__attfix then return end
  O.__attfix = true

  -- display modes supported by the monitor (unique WxH, sorted, >= 800x600)
  local modes = {}
  local n = AttTFix_ModeCount()
  for i = 0, n - 1 do
    local w, h = AttTFix_Mode(i)
    modes[#modes + 1] = { w, h }
  end
  -- make sure the current resolution is in the list (e.g. a custom one from graphic.cfg)
  local cw, ch = AttTFix_Current()
  local found = false
  for _, m in ipairs(modes) do if m[1] == cw and m[2] == ch then found = true end end
  if not found then
    modes[#modes + 1] = { cw, ch }
    table.sort(modes, function(a, b) if a[1] ~= b[1] then return a[1] < b[1] end return a[2] < b[2] end)
  end
  AttTFix.Modes = modes
  AttTFix_Log("options: " .. #modes .. " resolutions, current " .. cw .. "x" .. ch)

  local function curIndex()
    local w, h = AttTFix_Current()
    for i, m in ipairs(modes) do if m[1] == w and m[2] == h then return i - 1 end end
    return #modes - 1
  end
  local function label(i)
    local m = modes[i + 1]
    if m then return string.format("%dx%d", m[1], m[2]) end
    return "?"
  end
  local function refresh(self)
    if self.res_text then self.res_text:SetText(label(self.Resolution)) end
    local b = self.btns
    if b and b.Resolution_Down then
      if self.Resolution <= 0 then b.Resolution_Down:Disable() else b.Resolution_Down:Enable() end
    end
    if b and b.Resolution_Up then
      if self.Resolution >= #modes - 1 then b.Resolution_Up:Disable() else b.Resolution_Up:Enable() end
    end
  end


  -- extra rows in the options screen: cursor speed / camera speed (saved to AttTFix.ini by the DLL)
  local steps = { 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0 }
  local function nearest(v) local bi, bd = 4, 1e9 for i, x in ipairs(steps) do local d = math.abs(x - v) if d < bd then bi, bd = i, d end end return bi end
  local function arrow(self, x, y, sx, sy, tex, cb, size)
    local k = size / 47
    return Button:new(x * sx, y * sy, "contour", {
      Normal = { 0, 0, size * sx, size * sy, tex, nil },
      Selected = { -8 * k * sx, -8 * k * sy, 62 * k * sx, 62 * k * sy, "TickGlow.tga", "Glow", false },
      Disabled = { 0, 0, size * sx, size * sy, tex, "Default2DAlphaInactive", true },
      Sounds = { "Press2.wav", "" }
    }, self, cb)
  end
  -- Video panel compaction: while the original Options:Load runs, every Text/Button/Image created inside the
  -- Video panel (x >= 420, 84 <= y <= 470 in 800x600 units; the title at y=80 is kept) is scaled by F around
  -- (590, 85). The freed space at the bottom of the panel gets two full rows: cursor speed and camera speed.
  local F, AX, AY = 0.75, 590, 85
  local function inPanel(ux, uy) return ux >= 420 and uy >= 84 and uy <= 470 end
  local function makeCtorWrappers(sx, sy)
    local wrapped = {}
    local function tx(x) return (AX + (x / sx - AX) * F) * sx end
    local function ty(y) return (AY + (y / sy - AY) * F) * sy end
    local function scaleStates(st)
      if type(st) ~= "table" then return end
      for _, v in pairs(st) do
        if type(v) == "table" then
          for i = 1, 4 do if type(v[i]) == "number" then v[i] = v[i] * F end end
        end
      end
    end
    local function wrap(cls, name, fix)
      if type(cls) ~= "table" then return false end
      local orig = rawget(cls, "new")
      if type(orig) ~= "function" then return false end
      cls.new = function(c, ...)
        local a = { ... }
        local n = select("#", ...)
        if type(a[1]) == "number" and type(a[2]) == "number" and inPanel(a[1] / sx, a[2] / sy) then fix(a) end
        return orig(c, unpack(a, 1, n))
      end
      wrapped[#wrapped + 1] = { cls, orig }
      return true
    end
    local ok = wrap(Text, "Text", function(a)
      a[1], a[2] = tx(a[1]), ty(a[2]); if type(a[3]) == "number" then a[3] = a[3] * F end end)
    ok = wrap(Button, "Button", function(a) a[1], a[2] = tx(a[1]), ty(a[2]); scaleStates(a[4]) end) and ok
    ok = wrap(Image, "Image", function(a)
      a[1], a[2] = tx(a[1]), ty(a[2])
      if type(a[3]) == "number" then a[3] = a[3] * F end
      if type(a[4]) == "number" then a[4] = a[4] * F end end) and ok
    local function restore() for _, w in ipairs(wrapped) do w[1].new = w[2] end wrapped = {} end
    if not ok then restore() return false, nil end   -- all three or nothing
    return true, restore
  end

  -- FPS limit choices: { vsync, limit }; vsync uses the monitor refresh rate
  local fpsModes = { {1,0}, {0,30}, {0,60}, {0,90}, {0,120}, {0,144}, {0,165}, {0,240}, {0,0} }
  local function fpsIndex()
    local vs, lim = AttTFix_GetVideo()
    for i, m in ipairs(fpsModes) do if m[1] == vs and (vs == 1 or m[2] == lim) then return i end end
    return 1
  end
  local function fpsLabel(i, ru)
    local vs, lim, hz = AttTFix_GetVideo()
    local m = fpsModes[i]
    if m[1] == 1 then return "VSYNC " .. tostring(hz) end
    if m[2] == 0 then return ru and "НЕТ" or "OFF" end
    return tostring(m[2])
  end
  local function addInputControls(self, compact)
    local sx, sy = Config.ScreenWidth / 800, Config.ScreenHeight / 600
    local t = (LocalText and LocalText.tVideoO) or ""
    local ru = t:byte(1) ~= nil and t:byte(1) >= 192
    local function inputCtl(cx, y, size, font, name, idx, labelDy, valueDy, gap)
      Text:new(cx * sx, (y + labelDy) * sy, font * sy, name, "fStylo", "|", "colorDarkRed.tga")
      local val = Text:new(cx * sx, (y + valueDy) * sy, font * sy, "", "fStylo", "|", "colorDarkRed.tga")
      local function show() local v = { AttTFix_GetInput() } val:SetText(string.format("x%.2f", v[idx])) end
      local function step(d)
        local v = { AttTFix_GetInput() }
        local i = nearest(v[idx]) + d
        if i < 1 then i = 1 end
        if i > #steps then i = #steps end
        v[idx] = steps[i]
        AttTFix_SetInput(v[1], v[2])
        show()
      end
      arrow(self, cx - gap - size, y, sx, sy, "Left.tga", function() step(-1) end, size)
      arrow(self, cx + gap, y, sx, sy, "Right.tga", function() step(1) end, size)
      show()
    end
    if compact then
      -- row 1: FPS limit, same geometry as the scaled rows above
      local size = 47 * F
      local lx, rx = AX + (489 - AX) * F, AX + (644 - AX) * F
      local y = 345
      Text:new(AX * sx, (y + 23 * F) * sy, 14 * F * sy, ru and "ЛИМИТ FPS" or "FPS LIMIT", "fStylo", "|", "colorDarkRed.tga")
      local val = Text:new(AX * sx, (y + 37 * F) * sy, 14 * F * sy, "", "fStylo", "|", "colorDarkRed.tga")
      local cur = fpsIndex()
      local function show() val:SetText(fpsLabel(cur, ru)) end
      local function step(d)
        cur = cur + d
        if cur < 1 then cur = 1 end
        if cur > #fpsModes then cur = #fpsModes end
        AttTFix_SetFps(fpsModes[cur][1], fpsModes[cur][2])
        show()
      end
      arrow(self, lx, y, sx, sy, "Left.tga", function() step(-1) end, size)
      arrow(self, rx, y, sx, sy, "Right.tga", function() step(1) end, size)
      show()
      -- row 2: cursor | camera, value inline between the arrows ("CURSOR x0.75")
      local function inlineCtl(cx, y, name, idx)
        local val = Text:new(cx * sx, (y + 6) * sy, 9.5 * sy, "", "fStylo", "|", "colorDarkRed.tga")
        local function show() local v = { AttTFix_GetInput() } val:SetText(string.format("%s x%.2f", name, v[idx])) end
        local function step(d)
          local v = { AttTFix_GetInput() }
          local i = nearest(v[idx]) + d
          if i < 1 then i = 1 end
          if i > #steps then i = #steps end
          v[idx] = steps[i]
          AttTFix_SetInput(v[1], v[2])
          show()
        end
        arrow(self, cx - 44 - 24, y, sx, sy, "Left.tga", function() step(-1) end, 24)
        arrow(self, cx + 44, y, sx, sy, "Right.tga", function() step(1) end, 24)
        show()
      end
      inlineCtl(507, 397, ru and "КУРСОР" or "CURSOR", 1)
      inlineCtl(662, 397, ru and "КАМЕРА" or "CAMERA", 2)
      -- row 3: language (applied on the next start)
      if AttTFix_GetLang then
        local ly = 432
        local setting, active = AttTFix_GetLang()
        local names = { [0] = "РУССКИЙ", [1] = "ENGLISH" }
        local lval = Text:new(AX * sx, (ly + 6) * sy, 9.5 * sy, "", "fStylo", "|", "colorDarkRed.tga")
        local function lshow()
          local t = (ru and "ЯЗЫК: " or "LANGUAGE: ") .. names[setting]
          if setting ~= active then t = t .. (ru and "^ПОСЛЕ ПЕРЕЗАПУСКА" or "^AFTER RESTART") end
          lval:SetText(t)
        end
        local function lset() setting = 1 - setting; AttTFix_SetLang(setting); lshow() end
        arrow(self, AX - 72 - 24, ly, sx, sy, "Left.tga", lset, 24)
        arrow(self, AX + 72, ly, sx, sy, "Right.tga", lset, 24)
        lshow()
      end
    else
      inputCtl(507, 438, 28, 13, ru and "КУРСОР" or "CURSOR", 1, -7, 21, 30)
      inputCtl(662, 438, 28, 13, ru and "КАМЕРА" or "CAMERA", 2, -7, 21, 30)
    end
  end

  -- "Misc" panel, last row: fullscreen checkbox moves to the left half, the right half gets "intro videos"
  local miscState = {}
  local function relayoutMisc(sx, sy)
    local oT, oB = rawget(Text, "new"), rawget(Button, "new")
    if type(oT) ~= "function" or type(oB) ~= "function" then return nil end
    miscState.label, miscState.fixTick = false, false
    local function near(a, b) return type(a) == "number" and math.abs(a - b) < 0.5 end
    Text.new = function(c, x, y, ...)
      if near(x, 170 * sx) and near(y, 510 * sy) then x = 105 * sx; miscState.label = true end
      return oT(c, x, y, ...)
    end
    Button.new = function(c, x, y, kind, st, ...)
      if near(x, 250 * sx) and near(y, 490 * sy) and type(st) == "table" then
        x, y = 163 * sx, 495 * sy
        -- the English build hides this checkbox and has no tick texture for it
        if type(st.Contured) == "table" and st.Contured[5] == "dummy.tga" then
          st.Contured[5] = "Tick.tga"; st.Contured[6] = "Default2DAlpha"; miscState.fixTick = true
        end
        for _, v in pairs(st) do
          if type(v) == "table" then for i = 1, 4 do if type(v[i]) == "number" then v[i] = v[i] * 50 / 60 end end end
        end
      end
      return oB(c, x, y, kind, st, ...)
    end
    return function() Text.new, Button.new = oT, oB end
  end
  local function addIntroBox(self, sx, sy)
    local t = (LocalText and LocalText.tVideoO) or ""
    local ru = t:byte(1) ~= nil and t:byte(1) >= 192
    if not miscState.label then   -- English build: no fullscreen label, checkbox hidden
      Text:new(105 * sx, 510 * sy, 14 * sy, ru and "ПОЛНОЭКРАННЫЙ^РЕЖИМ" or "FULL^SCREEN", "fStylo", "|", "colorDarkRed.tga")
      local fb = self.btns and self.btns.IsFullScreen
      if fb and fb.Show then fb:Show() end
    end
    Text:new(272 * sx, 510 * sy, 14 * sy, ru and "ЗАСТАВКИ^ПРИ ЗАПУСКЕ" or "INTRO^VIDEOS", "fStylo", "|", "colorDarkRed.tga")
    local k = 50 / 60
    local b = Button:new(320 * sx, 495 * sy, "contour", {
      Normal = { 0, 0, 60 * k * sx, 60 * k * sy, "CheckBox.tga", nil },
      Selected = { 0, 0, nil, nil, "dummy", "dummy2D", false },
      Disabled = { 0, 0, nil, nil, "dummy", "dummy2D", false },
      Contured = { 12 * k * sx, 12 * k * sy, 36 * k * sx, 36 * k * sy, "Tick.tga", "Default2DAlpha", false },
      Sounds = { "Press2.wav", "" }
    }, self, function(s, btn)
      if btn:Contured() then btn:Unconture() else btn:Conture() end
      AttTFix_SetIntro(btn:Contured() and 0 or 1)
    end)
    if AttTFix_GetIntro() == 0 then b:Conture() end
  end

  local origLoad = O.Load
  O.Load = function(self, a1)
    self.Resolution = curIndex()
    local sx, sy = Config.ScreenWidth / 800, Config.ScreenHeight / 600
    local okw, compact, restore = pcall(makeCtorWrappers, sx, sy)
    if not okw then AttTFix_Log("options: compaction unavailable: " .. tostring(compact)); compact = false end
    local okm, unMisc = pcall(relayoutMisc, sx, sy)
    if not okm then AttTFix_Log("options: misc relayout error: " .. tostring(unMisc)); unMisc = nil end
    local okl, r = pcall(origLoad, self, a1)
    if unMisc then unMisc() end
    if restore then restore() end
    if okl and unMisc then
      local oki, erri = pcall(addIntroBox, self, sx, sy)
      if not oki then AttTFix_Log("options: intro checkbox error: " .. tostring(erri)) end
    end
    if not okl then error(r, 0) end
    self.Resolution = curIndex()
    self.ResolutionDef = self.Resolution
    refresh(self)
    local okc, errc = pcall(addInputControls, self, compact)
    AttTFix_Log("options: input controls " .. (compact and "(compact video panel)" or "(fallback layout)"))
    if not okc then AttTFix_Log("options: input controls error: " .. tostring(errc)) end
    AttTFix_Log("options opened: " .. label(self.Resolution) .. ", fullscreen=" .. tostring(self.Param and self.Param.IsFullScreen))
    return r
  end

  O._OnResolutionClk = function(self, btn, dir)
    if dir == "Resolution_Up" and self.Resolution < #modes - 1 then self.Resolution = self.Resolution + 1 end
    if dir == "Resolution_Down" and self.Resolution > 0 then self.Resolution = self.Resolution - 1 end
    refresh(self)
    AttTFix_Log("resolution -> " .. label(self.Resolution))
    if self.Resolution ~= self.ResolutionDef then self.isChanged = true end
    if self.Resolution == self.ResolutionDef and self.TexQuality == self.TexQualityDef
       and self.IsFullScreenDef == self.Param.IsFullScreen then
      self.isChanged = false
    end
  end

  local origApply = O._OnApply
  O._OnApply = function(self, ...)
    local m = modes[(self.Resolution or 0) + 1]
    local fs = (self.Param and self.Param.IsFullScreen) and true or false
    AttTFix_Log("apply: " .. label(self.Resolution or 0) .. ", fullscreen=" .. tostring(fs))
    -- DLL's ChangeSettings writes these values over the engine's legacy 5-mode table
    if m then AttTFix_SetPending(m[1], m[2], fs) end
    local idx = self.Resolution
    self.Resolution = 0
    local r = origApply(self, ...)
    self.Resolution = idx
    self.ResolutionDef = idx
    return r
  end
  AttTFix_Log("options patch installed")
end)
if not ok then AttTFix_Log("script error: " .. tostring(err)) end

-- ===================================================================== widescreen UI
-- Menu scenes (tagged __attfix_mode == 1 by the DLL: GUIScenes, SceneOptions, SceneLoad, SceneSave,
-- Infobox) are laid out on a centered 4:3 canvas; in-game scenes keep the original stretched layout.
local ok2, err2 = pcall(function()
  local cw, ch, ox, oy, rw, rh, enabled = AttTFix_Canvas()
  if enabled == 0 or (ox == 0 and oy == 0) then return end
  if not GUIScene then return end
  AttTFix = AttTFix or {}
  AttTFix.curOX, AttTFix.curOY = AttTFix.curOX or 0, AttTFix.curOY or 0
  AttTFix.RawSetPos = AttTFix.RawSetPos or {}

  -- scene objects are engine userdata: shift scene:SetPos() at the class level, only while a canvas scene loads
  local function classOf(real)
    local mt = getmetatable(real)
    local idx = type(mt) == "table" and mt.__index or nil
    if type(idx) ~= "table" then return nil end
    return idx
  end
  local function patchSceneClass(real)
    local idx = classOf(real)
    if not idx or AttTFix.RawSetPos[idx] ~= nil then return idx end
    local raw = rawget(idx, "SetPos")
    if type(raw) == "function" then
      AttTFix.RawSetPos[idx] = raw
      idx.SetPos = function(sc, x, y) return raw(sc, (x or 0) + AttTFix.curOX, (y or 0) + AttTFix.curOY) end
      AttTFix_Log("widescreen UI: scene class patched")
    else
      AttTFix.RawSetPos[idx] = false
    end
    return idx
  end
  local function setOrigin(real, x, y)
    local idx = patchSceneClass(real)
    local raw = idx and AttTFix.RawSetPos[idx]
    if raw then raw(real, x, y) end
  end
  local function setScreen(canvas)
    if type(Config) ~= "table" then return end
    if canvas then Config.ScreenWidth, Config.ScreenHeight = cw, ch
    else Config.ScreenWidth, Config.ScreenHeight = rw, rh end
  end

  -- temporarily add (dx, dy) to the position of every GUI element created (Image/Text/Button/Message/ToolTip ...)
  local function shiftElements(dx, dy)
    local saved = {}
    for _, cname in ipairs({ "Image", "Text", "Button" }) do
      local cls = rawget(_G, cname)
      local orig = type(cls) == "table" and rawget(cls, "new")
      if type(orig) == "function" then
        saved[#saved + 1] = { cls, orig }
        cls.new = function(c, ...)
          local a = { ... }; local n = select("#", ...)
          if type(a[1]) == "number" and type(a[2]) == "number" then a[1] = a[1] + dx; a[2] = a[2] + dy end
          return orig(c, unpack(a, 1, n))
        end
      end
    end
    return function() for _, w in ipairs(saved) do w[1].new = w[2] end end
  end

  local wrapped = 0
  for name, sc in pairs(GUIScene) do
    if type(sc) == "table" and type(sc.Load) == "function" and not sc.__attfix_ws then
      sc.__attfix_ws = true
      local origLoad = sc.Load
      local sceneName = tostring(name)
      sc.Load = function(self, ...)
        local canvas = (self.__attfix_mode == 1)
        AttTFix_Log("scene " .. sceneName .. " Load" .. (canvas and " (canvas)" or ""))
        local real = self.scene
        local unwrap = nil
        if canvas and self.isChild then
          -- child dialogs: the engine itself centers them by their background size (bgndWidth = canvas width),
          -- and their scene object belongs to the parent (moving it moved the world HUD) -> only the canvas size
          setScreen(true)
        elseif canvas then
          setScreen(true)
          AttTFix.curOX, AttTFix.curOY = ox, oy
          if real ~= nil then
            local okp, errp = pcall(setOrigin, real, ox, oy)
            if not okp then AttTFix_Log("scene " .. sceneName .. " origin error: " .. tostring(errp)) end
          end
          if not self.isChild then
            -- black bars outside the canvas (cover whatever the game rendered there before)
            local okb, errb = pcall(function()
              if ox > 0 then
                Image:new(-ox, 0, ox, rh, "dummy.tga", "2DFillBlack")
                Image:new(cw, 0, rw - cw - ox + 1, rh, "dummy.tga", "2DFillBlack")
              end
              if oy > 0 then
                Image:new(-ox, -oy, rw, oy, "dummy.tga", "2DFillBlack")
                Image:new(-ox, ch, rw, rh - ch - oy + 1, "dummy.tga", "2DFillBlack")
              end
            end)
            if not okb then AttTFix_Log("scene " .. sceneName .. " bars error: " .. tostring(errb)) end
          end
        end
        local ok, r1, r2 = pcall(origLoad, self, ...)
        if unwrap then unwrap() end
        AttTFix.curOX, AttTFix.curOY = 0, 0
        setScreen(false)
        if not ok then
          AttTFix_Log("scene " .. sceneName .. " Load error: " .. tostring(r1))
          error(r1, 0)
        end
        return r1, r2
      end
      wrapped = wrapped + 1
    end
  end
  if wrapped > 0 then AttTFix_Log(string.format("widescreen UI: canvas %dx%d at +%d,+%d on %dx%d, %d scenes wrapped", cw, ch, ox, oy, rw, rh, wrapped)) end
end)
if not ok2 then AttTFix_Log("widescreen script error: " .. tostring(err2)) end

-- ===================================================================== original layout bugs
-- Battle victory report: gold/experience lines use the horizontal scale for their Y position
-- (400 * sx instead of 400 * sy) -> on wide screens they slide below the book.
local ok3, err3 = pcall(function()
  local sc = GUIScene and GUIScene.TacticalEndVictory
  if type(sc) ~= "table" or type(sc.Load) ~= "function" or sc.__attfix_vfix then return end
  sc.__attfix_vfix = true
  local origLoad = sc.Load
  sc.Load = function(self, ...)
    local W, H = Config.ScreenWidth, Config.ScreenHeight
    local sx, sy = W / 800, H / 600
    local orig = Text and rawget(Text, "new")
    if type(orig) ~= "function" or math.abs(sx - sy) < 1e-4 then return origLoad(self, ...) end
    Text.new = function(c, x, y, ...)
      if type(y) == "number" then
        for _, v in ipairs({ 400, 416 }) do
          if math.abs(y - v * sx) < 0.01 then y = v * sy break end
        end
      end
      return orig(c, x, y, ...)
    end
    local ok, r1, r2 = pcall(origLoad, self, ...)
    Text.new = orig
    if not ok then error(r1, 0) end
    return r1, r2
  end
  AttTFix_Log("layout fix: victory report gold/exp position")
end)
if not ok3 then AttTFix_Log("layout fix error: " .. tostring(err3)) end

-- ===================================================================== "mod active" label in the main menu
local ok4, err4 = pcall(function()
  local sc = GUIScene and GUIScene.MainMenu
  if type(sc) ~= "table" or type(sc.Load) ~= "function" or sc.__attfix_label then return end
  sc.__attfix_label = true
  local origLoad = sc.Load
  sc.Load = function(self, ...)
    local r1, r2 = origLoad(self, ...)
    pcall(function()
      local cw, ch, ox, oy, rw, rh, enabled = AttTFix_Canvas()
      if enabled == 0 then ox, oy = 0, 0 end
      local t = (LocalText and LocalText.tVideoO) or ""
      local ru = t:byte(1) ~= nil and t:byte(1) >= 192
      local size = rh / 600 * 9
      local txt = "AttTFix " .. tostring(AttTFix_Version or "?") .. (ru and "  -  мод активен" or "  -  mod active")
      Text:new(rw - ox - size * 0.6, rh - oy - size * 1.5, size, txt, "fCenturyGothic", ">", "colorYellow.tga")
    end)
    return r1, r2
  end
end)
if not ok4 then AttTFix_Log("menu label error: " .. tostring(err4)) end
