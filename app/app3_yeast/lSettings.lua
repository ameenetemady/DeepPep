local lSettings = {}

do
  lSettings.strBaseDir = "./sparseData2"
  lSettings.strFilenameTarget = string.format("%s/target.csv", lSettings.strBaseDir)
  lSettings.strFilenameMetaInfo = string.format("%s/metaInfo.csv", lSettings.strBaseDir)
  lSettings.strFilenameProtRef = string.format("./protRef/yeast_ref5.csv", lSettings.strBaseDir)
  lSettings.strFilenameProtInfo = string.format("%s/protInfo.csv", lSettings.strBaseDir)
  lSettings.strFilenameExperiment1Obj = string.format("./model/experiment_1.obj" )
  lSettings.nRows=11601

  return lSettings
end

