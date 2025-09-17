import os
import datetime
import os
import pathlib
import glob
import datetime
import shutil
import PyPDF2

Path = r"C:\Users\Camel\Downloads\merger"

timestamp = str(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
targetDir = Path+"\\Merge_"+timestamp
if not os.path.exists(targetDir):
	#create target directory
	os.mkdir(targetDir)

files = glob.glob(Path+r"\*.pdf")
for file in files:
    os.rename(file,targetDir+"\\"+os.path.basename(file))
 
#merge pdf
from PyPDF2 import PdfMerger 
mergeFiles =os.listdir(targetDir)
merger = PdfMerger()
for mFile in mergeFiles:
    merger.append(open(targetDir+"\\"+mFile,'rb'))
with open(Path+"\\MergeResult-"+timestamp+".pdf","wb") as resFile:
    merger.write(resFile)
