from pathlib import Path
import time
import re
import os
import traceback

################################################################################################
#                                    F-Chat 3.0 Log Parser                                     #
#                                      Author: GyroTech                                        #
#                                                                                              #
#                                       1.1.1- 11/30/2022                                      #
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
flistDirectory = "C:\\Users\\jdavis\\Documents\\New folder\\Test" # Link to flist log directory
logDirectory = "C:\\Users\\jdavis\\Documents\\New folder\\Test2" # Link to where you'd like the logs to go.
logExt = ".log"
splitBy = "month" #accepts Day, Month, Year and None
folderStructure = 1 # 0 means you're pointing directly to the character you want logs from.
                    # For 1 or 2 point to the root f-list logs folder.
                    # 1 means logs will be outputtted as {Your character}/{Other character}
                    # 2 means logs will be outputted as {Other Character}/{Your Character}



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
runTime = lastrun
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
if folderStructure == 0:
    flistCharDirectory = [[flistDirectory,"",""]]
elif folderStructure == 1:
    flistCharDirectory = os.listdir(flistDirectory)
    temp1 = [flistDirectory + "\\" + f + "\\logs" for f in flistCharDirectory ]
    temp2 = ["\\" + f for f in flistCharDirectory]
    flistCharDirectory = [[temp1[i], temp2[i], ""] for i in range(len(temp1))]
elif folderStructure == 2:
    flistCharDirectory = os.listdir(flistDirectory)
    temp1 = [flistDirectory + "\\" + f + "\\logs" for f in flistCharDirectory ]
    temp2 = ["\\" + f for f in flistCharDirectory]
    flistCharDirectory = [[temp1[i], "", temp2[i]] for i in range(len(temp1))]
else:
    raise Exception("Folder Structure flag is invalid")
for char in flistCharDirectory:    
    try:
        for f in os.listdir(char[0]):
            if re.search("\.", f):
                continue
            try:
                with open(char[0] +"\\"+ f, "rb") as fr:
                    fileLength = os.path.getsize(char[0] +"\\"+ f)
                    with open(char[0] +"\\"+ f+".idx", "rb") as idx:
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
                        os.makedirs(logDirectory+char[1]+"\\", exist_ok=True)
                        os.makedirs(logDirectory+char[1]+"\\"+fName+"\\", exist_ok=True)
                        os.makedirs(logDirectory+char[1]+"\\"+fName+char[2]+"\\", exist_ok=True)
                        Path(logDirectory+char[1]+"\\"+fName+char[2]+"\\"+fileTime+fName+logExt).touch()
                        with open(logDirectory+char[1]+"\\"+fName+char[2]+"\\"+fileTime+fName+logExt,"a", errors='ignore') as fw:
                            while True:
                                if lineTime > runTime:
                                    runTime = lineTime
                                # Lines are of the following format:
                                # {time}{action}{namelength}{Name}{messagelength}{message}{backwardsTraversalLength}
                                # time = 4 bytes, little endian, Unix time
                                # action = 0x01 for action, 0x00 for speech
                                # Name length = 1 byte
                                # messagelength = 2 bytes, little endian
                                # backwardsTraversalLength 2 bytes, little endian. Total lenght of all bytes in the line.
                                currentLine = logLine()
                                currentLine.setTime(lineTime)
                                currentLine.isAction(fr.read(1))
                                characterOffset = int.from_bytes(fr.read(1),"big")
                                if characterOffset == 0:
                                    #Fix for F-list occasionally leaving strings of 0x00 when the logger breaks.
                                    while characterOffset == 0:
                                        characterOffset = int.from_bytes(fr.read(1),"big")
                                    inline = 1
                                    count = 1
                                    while inline < 3:
                                        characterOffset = int.from_bytes(fr.read(1),"big")
                                        if characterOffset > 1:
                                            inline += 1
                                        else:
                                            inline = 0
                                        count += 1
                                    if count == 3:
                                        characterOffset = int.from_bytes(fr.read(1),"big")
                                        if characterOffset < 2: # 0 or 1 means its an action next, so our first byte is a 0.
                                            fr.seek(-5,1)
                                        else:
                                            fr.seek(-4,1)
                                    else:
                                        fr.seek(-8,1)
                                    lineTime = int.from_bytes(fr.read(4),"little")
                                    continue
                                currentLine.setCharacter(fr.read(characterOffset).decode("utf-8", "ignore"))
                                messageOffset = int.from_bytes(fr.read(2),"little")
                                currentLine.setMessage(fr.read(messageOffset).decode("utf-8", "ignore"))
                                fr.read(2) #Last 2 bytes for reverse traversal
                                currentLine.encodeLine()
                                fw.writelines(currentLine.encodedLine)    
                                lineTime = int.from_bytes(fr.read(4),"little")
                                if time.strftime(splitFormat, time.localtime(lineTime)) != fileTime:
                                    if lineTime == 0: 
                                        # Fix for broken slimcat log imports
                                        lineTime = currentLine.messageTimeRaw
                                    break
            except OSError:
                traceback.print_exc()
                continue
    except OSError:
                continue
open(logDirectory +"\\lastrun.txt","a").writelines(f"{runTime}\n")
        
