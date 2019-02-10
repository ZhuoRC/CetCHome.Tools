
Path = r"C:\Users\Camel\Pictures\ControlCenter4\Scan"
CounterChar = "_"
FileType = "pdf"
AutoMergePdf = 1
Debug = 0


import os
import pathlib
import glob
import datetime
import shutil

#debug
if Debug :
	deg_files = glob.glob(Path+"\\debug\*."+FileType)
	for deg_file in deg_files:
		shutil.copy(deg_file,Path)


#create target folder
timestamp = str(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
targetDir = Path+"\\MergeScan_"+timestamp
if not os.path.exists(targetDir):
	#create target directory
	os.mkdir(targetDir)

#only handle pdf files
files = glob.glob(Path+r"\*."+FileType)
if len(files)%2 == 1 :
	raise RuntimeError(str(len(files))+" files cannot be paired!")

#re-index all the scan files
loop = 1
for file in files:
	fileBasename = os.path.basename(file)
	#get fileIndex
	fileIndex = file.split(CounterChar)[-1].split(".")[0]
	if loop <= (len(files))/2:
		#odd
		newIndex = loop*2-1
	else:
		#even
		newIndex = int(len(files)) - (loop-int(len(files)/2)-1)*2
	
	newFilename = fileBasename.replace(fileIndex,str(newIndex)+"_"+fileIndex)

	print(loop, fileBasename,"-->",newFilename)
	os.rename(file,targetDir+"\\"+newFilename)

	loop+=1

#merge pdf
if AutoMergePdf:
	from PyPDF2 import PdfFileMerger
	mergeFiles = sorted(os.listdir(targetDir),key=lambda x: int(os.path.splitext(x.split('_')[1])[0]))
	merger = PdfFileMerger()
	for mFile in mergeFiles:
		merger.append(open(targetDir+"\\"+mFile,'rb'))
	with open(Path+"\\MergeResult-"+timestamp+".pdf","wb") as resFile:
		merger.write(resFile)
