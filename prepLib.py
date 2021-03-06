from Bio import SeqIO
import os
import csv
import statistics as stat
import re
from multiprocessing.dummy import Pool as ThreadPool

# Description: break the fasta file into multiple proteins, only save the ones provided in protsDic
# Note: previous version (which some callers may be using), took nameID option to only save part of the name (separated by "|").
def breakFasta(strFastaFilename, strProtRefsDir, protsDic = None):

  # create dir if missing
    if not os.path.exists(strProtRefsDir):
        os.makedirs(strProtRefsDir)

  # read from fasta file and generate one file for each protein
    counter = 0
    for currRecord in SeqIO.parse(strFastaFilename, "fasta"):
        if (protsDic is None) or (currRecord.name in  protsDic): # means: if protsDic is provided, then verify
            strFilePath = '{!s}/{!s}.txt'.format(strProtRefsDir, currRecord.name )
            with open(strFilePath, 'w') as bfProt:
                bfProt.write(str(currRecord.seq))

            counter += 1

    print('read and generated {:d} files'.format(counter))

def loadPepProbsFromCsv(strFilePath, delimiter, pepId, probId):
    listPeptideProb = []
    with open(strFilePath, "r") as bfCsv:
        csvReader = csv.reader(bfCsv, delimiter = delimiter, skipinitialspace=True)
        counter = 0
        for row in csvReader:
            listPeptideProb.append([row[pepId], float(row[probId])])

    return listPeptideProb

def loadUniqProtsDicFromCsv(strFilePath, delimiter, protColId):
    protsDic = {}
    with open(strFilePath, "r") as bfCsv:
        csvReader = csv.reader(bfCsv, delimiter = delimiter, skipinitialspace=True)
        for row in csvReader:
            protsDic[row[protColId]] = True

    return protsDic

# Description: Load protein, peptide, and probablity info into single dictionary
# Return: 
#   1) Dictionary of proteins pointed to the corresponding peptides and probabilities
#   2) Dictionary of peptides with associated probababilities
def loadProtPeptideDic(strFilePath, delimiter = "\t", protColId = 1, pepColId = 0, probColId = 2):
    protDic = {}
    pepDic = {}

    with open(strFilePath, "r") as bfCsv:
        csvReader = csv.reader(bfCsv, delimiter = delimiter, skipinitialspace=True)
        for row in csvReader:
            strPep = row[pepColId]
            strProt = row[protColId]
            dProb = float(row[probColId])

            # update peptide info
            pepInfo = pepDic.get(strPep)
            if pepInfo is None:
                pepInfo = [len(pepDic), strPep, dProb]
                pepDic[strPep] = pepInfo
            else:
                pepInfo[2] = max(dProb, pepInfo[2]) # Note: allways using 'max', if mean need a little more work
            
            
            # update protInfo
            protInfo = protDic.get(strProt)
            if protInfo is None:
                protInfo = {}
                protDic[strProt] = protInfo

            protInfo[strPep] = pepInfo
        
        return protDic, pepDic
            

def consolidatePepProbs(listPeptideProb):
    dicAll = {}

    # a) load all into dic
    for row in listPeptideProb:
      strPeptide = row[0]
      dProb = row[1]

      if strPeptide not in dicAll:
          dicAll[strPeptide] = list()

      dicAll[strPeptide].append(float(dProb))


    # b) consolidate
    listPeptideProbRes = []
    for strPeptide, listProb in dicAll.items():
      #        listPeptideProbRes.append([strPeptide, stat.median(listProb)]) #ToDo: uncomment after removing next line if you want median
        listPeptideProbRes.append([strPeptide, max(listProb)])

    listPeptideProbRes.sort()
    return listPeptideProbRes

def getProtRefFileNames(strBaseProtRefsPath):
    listProtFileName = os.listdir(strBaseProtRefsPath)
    return listProtFileName

def fuFindOnes(strProtSeq, strPepSeq):
    listMatches = []
    for match in re.finditer(strPepSeq, strProtSeq):
        start, end = match.span()
        listMatches = listMatches + [[start, end-start]]
    
    return listMatches

def fuFindPeptideMatch(strBaseProtRefsPath, strProtFileName, listPeptideProb):
    strProtFileName = strBaseProtRefsPath + '/' + strProtFileName

    listOnes = []

    with open(strProtFileName, 'r') as bfProtFile:
        strProtSeq = bfProtFile.read().strip()

        for item in listPeptideProb:
            i = item[0]
            strPepSeq = item[1]
            listPeptideOnes = fuFindOnes(strProtSeq, strPepSeq)

            if listPeptideOnes and  len(listPeptideOnes) > 0:
                listOnes.append([i, listPeptideOnes])

    return listOnes

def fuSaveProtPepOnes(strDir, strProtFileName, listProtPepOnes):
    strFilePath = strDir + '/' + strProtFileName

    with open(strFilePath, 'w') as bfFile:
        for row in listProtPepOnes:
            if len(row)>2:
                print("####### ******************************* Look:" + strProtFileName )
            bfFile.write('{:d}:'.format(row[0]) )
            for listRange in row[1]:
                bfFile.write('|{:d},{:d}'.format(listRange[0], listRange[1]))
            bfFile.write("\n")

def fuRunAllProt(listProtFileName, strBaseProtRefsPath, strSparseDir, protsDic):

    def fuRunProt(strProtFileName):
      print("started: " + strProtFileName)
      # remove the trailing ".txt" from filename
      strProtName = strProtFileName[0:-4]
      listPeptideProb = protsDic[strProtName].values()

      listProtPepOnes = fuFindPeptideMatch(strBaseProtRefsPath , strProtFileName, listPeptideProb)
      if len(listProtPepOnes) > 0:
          fuSaveProtPepOnes(strSparseDir, strProtFileName, listProtPepOnes)
          print("saved:" + strProtFileName)
          return 1
      else:
          return 0

    '''    
    isSave = fuRunProt(listProtFileName[1])
    print(listProtRefFileName[1])
    print(isSave)
    '''    
 
    print(listProtFileName)
    pool = ThreadPool(32)
    res = pool.map(fuRunProt, listProtFileName)
    pool.close() 
    pool.join() 
    print(res)

def fuGetProtLength(strFilePath):
    with open(strFilePath, 'r') as bfFile:
        nLength = len(bfFile.readline())
        return nLength

def fuSaveMetaInfo(strBasePath, strMetaInfoFilename, strBaseProtRefsPath):
    listProtFiles = [i for i in  os.listdir(strBasePath) if i.endswith('.txt') ]
    with open(strMetaInfoFilename, 'w') as bfFile:
        for strProtFileName in listProtFiles:
            strFilePath = '{!s}/{!s}'.format(strBaseProtRefsPath, strProtFileName)
            nProtWidth = fuGetProtLength(strFilePath)
            bfFile.write('{!s},{:d}\n'.format(strProtFileName, nProtWidth))

def fuSavePepProbsTargetFromList(strFilePath, listPeptideProb):
    with open(strFilePath, 'w') as bfFile:
        for row in listPeptideProb:
            dProb = row[1]
            bfFile.write('{:.6f}\n'.format(dProb))

    return


#sparseData3 (cleavage sites) related functions
def getEdges(lSegments):
    edges = {}
    for sLine in lSegments:
        for s in sLine[1]:
            sL = s[0]
            sR = s[1] + sL
            edges[sL] = True
            edges[sR] = True

    return sorted(list(edges.keys()))
    
def getOneEdgeMatch(pepMatches, edges):

    eMatchesOne = []
    for pM in pepMatches:
        eL = pM[0]
        idx = edges.index(eL)
        eMatchesOne += [[idx, 1]]

        eR = eL + pM[1]
        idx = edges.index(eR)
        eMatchesOne += [[idx, 1]]

    return eMatchesOne

def getEdgeMatches(edges, flistProtPepOnes):
    eMatches = []
    for s in flistProtPepOnes:
        eMatchesOne = getOneEdgeMatch(s[1], edges)
        eMatches += [[ s[0], eMatchesOne]]

    return eMatches

def fuFindPeptideMatch_CleavageSites(strBaseProtRefsPath , strProtFilename, listPeptideProb):
    flistProtPepOnes = fuFindPeptideMatch(strBaseProtRefsPath, strProtFilename, listPeptideProb)
    edges = getEdges(flistProtPepOnes)
    eMatches = getEdgeMatches(edges, flistProtPepOnes)

    return eMatches, len(edges)

def fuRunAllProt_CleavageSites(listProtFileName, strBaseProtRefsPath, strSparseDir, listPeptideProb):
    def fuRunProt(strProtFileName):
        print("#start:" + strProtFileName)
        listProtPepOnes, nEdges = fuFindPeptideMatch_CleavageSites(strBaseProtRefsPath , strProtFileName, listPeptideProb)
        if len(listProtPepOnes) > 0:
            fuSaveProtPepOnes(strSparseDir, strProtFileName, listProtPepOnes)
            print("saved:" + strProtFileName)
            return [strProtFileName, nEdges]

    if len(listProtFileName) < 2 : # for test
        fuRunProt(listProtFileName[0])
        return
    
    #print(listProtFileName)
    pool = ThreadPool(16)
    res = pool.map(fuRunProt, listProtFileName)
    pool.close() 
    pool.join() 
    
    return list(filter(None.__ne__, res))

def fuSaveMetaInfo_CleavageSites(strFilename, metaInfo):
    with open(strFilename, 'w') as bfFile:
        for info in metaInfo:
            bfFile.write('{!s},{:d}\n'.format(info[0], info[1]))
