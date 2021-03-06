require 'nn'

require('../../CDataLoader.lua')
local exprSetting = require('./lSettings.lua')
local trainerPool = require('../../deposTrainerPool.lua')

local cDataLoader = CDataLoader.new(exprSetting)

--[[
local taX_Sparse0 = cDataLoader:loadSparseInputSingle("p0.sprs")
local nWidth0=393
local module0 = nn.SparseLinear(nWidth0, 1, true)
local output0 = module0:forward(taX_Sparse0)
--]]

local taMetaInfo = cDataLoader:loadSparseMetaInfo()

-- 1) Build the layer0
local nUnitWidthLayer0 = 1
local mLayer0 = nn.ParallelTable()
local nParallels = 0
for key, taFileInfo in pairs(taMetaInfo) do
  mLayer0:add(nn.SparseLinear(taFileInfo.nWidth, nUnitWidthLayer0, true))
  nParallels = nParallels + 1
end

-- 2) Build the rest of the FNN:
local mNet = nn.Sequential()
mNet:add(mLayer0)
mNet:add(nn.JoinTable(2))
mNet:add(nn.Linear(nParallels, 1))

-- 3) Load the Sparse Input:
local taInput = {}
for key, taFileInfo in pairs(taMetaInfo) do
  local taOneInput = cDataLoader:loadSparseInputSingle(taFileInfo.strFilename)
  table.insert(taInput, taOneInput)
end

-- 4) Load the Target
local teTarget = cDataLoader:loadTarget()

-- 5) Train
  local dTrainErr = trainerPool.trainSparseInputNet(mNet, taInput, teTarget)
  print("training error:" .. dTrainErr) 
