-- Description: takes SparseBlock columns (with ) and perfoms a Linear 
-- 							operation to map them into a dense matrix which it's 
-- 							width is specified as nOutputWidth


local SparseBlockToDenseLinear, parent = torch.class('nn.SparseBlockToDenseLinear', 'nn.Module')

function SparseBlockToDenseLinear:__init(nOutputWidth, bias)
	bias = bias or false
	assert(bias == false, "Only supporting zero bias for now!")

	self.nOutputWidth = nOutputWidth
end

function SparseBlockToDenseLinear:pri_ensureWeight(input)
	if self.weight ~= nil then
		return
	end

	local nColumns = table.getn(input.taData)
	self.weightMeta = torch.LongTensor(nColumns)

	-- find the size:
	local nTotalWeightSize = 0
	for i=1, nColumns do
		local taInputCurr = input.taData[i]
		local nWidth = taInputCurr.teValue:size(2)
		self.weightMeta[i] = nTotalWeightSize + 1
		nTotalWeightSize = nTotalWeightSize + nWidth
	end

	-- allocate:
	self.weight = torch.zeros(nTotalWeightSize, self.nOutputWidth)
	self.gradWeight = torch.zeros(nTotalWeightSize, self.nOutputWidth)

	self:reset()
end

function SparseBlockToDenseLinear:reset(stdv)

		if stdv then
			stdv = stdv * math.sqrt(3)
		else
			stdv = 1./math.sqrt(self.weight:size(1))
		end

		self.weight:uniform(-stdv, stdv)
end

function SparseBlockToDenseLinear:pri_getSubW(i, teW)
	local nStart = self.weightMeta[i]
	local nLenght = -1  
	if i < self.weightMeta:size(1) then
		nLenght = self.weightMeta[i+1] - nStart
	else -- the last one, is different
		nLenght = teW:size(1) - nStart + 1
	end

	return teW:narrow(1, nStart, nLenght)
end

function SparseBlockToDenseLinear:pri_getSubWeight(i)
	return self:pri_getSubW(i, self.weight)
end

function SparseBlockToDenseLinear:pri_getSubGradWieght(i)
	return self:pri_getSubW(i, self.gradWeight)
end

function SparseBlockToDenseLinear:pri_ensureOutput(input)
	if self.output ~= nil then
		return
	end

	self.output = torch.zeros(input.nBatchSize, self.nOutputWidth)
	-- the following only done to support matrix operation only accumulation of results (instead of iterating using a for loop), hence maybe avoided
	self.outputBufferA = torch.zeros(input.nBatchSize, self.nOutputWidth) -- used for initial output result of each column (allocated for maximum possible size)
	self.outputBufferB = torch.zeros(input.nBatchSize, self.nOutputWidth) -- used for holding "scatter" results, to be added to self.output
end

function SparseBlockToDenseLinear:pri_updateOutput_column(taInput, teWeight)
	self.outputBufferA:zero()
	self.outputBufferB:zero()

	-- calculate the output for non-Sparse blocks
	local teInput = taInput.teValue
	local nRows = teInput:size(1)
	local teOutput = self.outputBufferA:narrow(1, 1, nRows)
	teOutput:addmm(teInput, teWeight)
	
	-- copy result to buffer
	print(taInput.teRowIdx)
	local teDstIdx = torch.expand(taInput.teRowIdx, nRows, self.nOutputWidth)
	print(teDstIdx)
	self.outputBufferB:scatter(1, teDstIdx, teOutput)

	-- add buffer to output
	self.output:add(self.outputBufferB)
end

function SparseBlockToDenseLinear:updateOutput(input)
	self:pri_ensureWeight(input)
	self:pri_ensureOutput(input)

	local nColumns = table.getn(input.taData)
	for i=1, nColumns do
		self:pri_updateOutput_column(input.taData[i], 
																 self:pri_getSubWeight(i))
	end

	return self.output
end