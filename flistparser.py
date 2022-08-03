from pathlib import Path
import time
import re
import os
import traceback

################################################################################################
#                                    F-Chat 3.0 Log Parser                                     #
#                                      Author: GyroTech                                        #
#                                                                                              #
#                                       1.0-8/3/2022                                           #
#                                                                                              #
# This script parses out the database logs that fchat spits out, and then turns them into      #
# plain text. The script automatically remembers when you last ran it, and will append to      #
# existing logs. Note, this only works for the desktop version of f-chat.                      #
#                                                                                              #
# Usage: Update the variables below and then run it. If you want to rerun the full export,     #
# delete the lastrun.txt file in your plain text log folder. Note, this script appends to the  #
# logs, so it will duplicate unless you delete the folders you intend to rerun.                # 
#                                                                                              #
################################################################################################


#Variables for log locations
flistDirectory = "C:\\Users\\user\\Documents\\New folder\\Test"
logDirectory = "C:\\Users\\user\\Documents\\New folder\\Test2"
logExt = ".log"
splitBy = "month" #accepts Day, Month, Year and None



class logLine():
    def __init__(self):
        self.messageTime = ""
        self.action = ""
        self.notAction = ""
        self.character = ""
        self.message = ""
        self.encodedLine =""
        self.messageTimeRaw = 1
    def setTime(self,dt):
        self.messageTime = time.strftime("%Y-%m-%d %H:%M",time.localtime(dt))
        self.messageTimeRaw = dt
    def isAction(self,ia):
        if ia:
            self.action = "*"
        else:
            self.notAction = ":"
    def setCharacter(self, cr):
        self.character = cr
    def setMessage(self, ms):
        self.message = ms
    def encodeLine(self):
        self.encodedLine = "["+self.messageTime+"]"+ self.action+self.character+self.notAction+ " " +self.message+ "\n"




Path(logDirectory + "\\lastrun.txt").touch()
try:
    lastrun = open(logDirectory +"\\lastrun.txt").readlines()[-1]
    lastrun = int(lastrun)
except  IndexError:
     lastrun=1
runTime = int(time.time())
if splitBy.lower() == "year":
    splitFormat = "%Y "
elif splitBy.lower() == "month":
    splitFormat = "%Y-%m "
elif splitBy.lower() == "day":
    splitFormat = "%Y-%m-%d "
elif splitBy.lower() == "none":
    splitFormat = ""
else:
    raise Exception("SplitBy not a valid value")      
for f in os.listdir(flistDirectory):
    if re.search("\.", f):
        continue
    try:
        with open(flistDirectory +"\\"+ f, "rb") as fr:
            fileLength = os.path.getsize(flistDirectory +"\\"+ f)
            with open(flistDirectory +"\\"+ f+".idx", "rb") as idx:
                offset = int.from_bytes(idx.read(1),"big")
                fName = idx.read(offset).decode("utf-8")
                fName = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", fName).strip()
                print(f +", " + fName)
            if lastrun != 1:
                fr.seek(0,2)
                while True:
                    fr.seek(-2,1)
                    lineLength = int.from_bytes(fr.read(2),"little")+2
                    fr.seek(-lineLength,1)
                    lineTime = int.from_bytes(fr.read(4),"little")
                    fr.seek(-4,1)
                    if lineTime < lastrun:
                        fr.seek(lineLength,1)
                        break
            lineTime = int.from_bytes(fr.read(4),"little")
            while fr.tell() < fileLength:
                fileTime = time.strftime(splitFormat,time.localtime(lineTime))
                os.makedirs(logDirectory+"\\"+fName+"\\", exist_ok=True)
                Path(logDirectory+"\\"+fName+"\\"+fileTime+fName+logExt).touch()
                with open(logDirectory+"\\"+fName+"\\"+fileTime+fName+logExt,"a", errors='ignore') as fw:
                    while True:
                        currentLine = logLine()
                        currentLine.setTime(lineTime)
                        currentLine.isAction(fr.read(1))
                        characterOffset = int.from_bytes(fr.read(1),"big")
                        currentLine.setCharacter(fr.read(characterOffset).decode("utf-8", "ignore"))
                        messageOffset = int.from_bytes(fr.read(2),"little")
                        currentLine.setMessage(fr.read(messageOffset).decode("utf-8", "ignore"))
                        fr.read(2) #Last 2 bytes for reverse traversal
                        currentLine.encodeLine()
                        fw.writelines(currentLine.encodedLine)    
                        lineTime = int.from_bytes(fr.read(4),"little")
                        if time.strftime(splitFormat, time.localtime(lineTime)) != fileTime:
                            if lineTime == 0:
                                lineTime = currentLine.messageTimeRaw
                            break
    except Exception:
        traceback.print_exc()
        continue
open(logDirectory +"\\lastrun.txt","a").writelines(f"{runTime}\n")
        