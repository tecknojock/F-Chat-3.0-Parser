from pathlib import Path
import time
import re
import os
import traceback

################################################################################################
#                                    F-Chat 3.0 Log Parser                                     #
#                                      Author: GyroTech                                        #
#                                                                                              #
#                                       1.1.3- 12/14/2025                                      #
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
flistDirectory = "D:\\Users\\Tecknojock\\Documents\\Test" # Link to flist log directory
logDirectory = "D:\\Users\\Tecknojock\\Documents\\Test2" # Link to where you'd like the logs to go.
logExt = ".log"
splitBy = "Month" #accepts Day, Month, Year and None
folderStructure = 0 # 0 means you're pointing directly to the character you want logs from.
                    # For 1 or 2 point to the root f-list logs folder.
                    # 1 means logs will be outputtted as {Your character}/{Other character}
                    # 2 means logs will be outputted as {Other Character}/{Your Character}


namepattern = r"[a-zA-Z0-9 _-]+"


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

def findLineStart (fr):
    #Fix for F-list occasionally leaving strings of 0x00 when the logger breaks.
    # Improved fix is now logger mistake agnostic. It will seek until it finds a valid user name.
    try:
        while fr.tell() < fileLength:
            characterOffset = int.from_bytes(fr.read(1),"big") #last Date byte
            if characterOffset > 1 or characterOffset == 0: 
                characterOffset = int.from_bytes(fr.read(1),"big") #Action Bite
                if characterOffset < 2: 
                    characterOffset = int.from_bytes(fr.read(1),"big") #character Byte
                    if characterOffset < 21 and characterOffset > 1 :
                        character = (fr.read(characterOffset).decode("ISO-8859-1", "ignore"))
                        if re.fullmatch(namepattern, character):
                            fr.seek(-4-1-1-characterOffset, 1)
                            break
                        elif fr.tell() >= fileLength:
                            raise(Exception("End of File"))
                        else:
                            fr.seek(-2-characterOffset,1)
                    elif fr.tell() >= fileLength:
                        raise(Exception("End of File"))
                    else:
                        fr.seek(-2,1)
                elif fr.tell() >= fileLength:
                    raise(Exception("End of File"))
                else: 
                    fr.seek(-1,1)
    except:
        return "EoF"


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
            if f == "_":
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
                        #check last line to see if logger needs to run
                        fr.seek(0,2)
                        fr.seek(-2,1)
                        lineLength = int.from_bytes(fr.read(2),"little")+2
                        fr.seek(-lineLength,1)
                        lineTime = int.from_bytes(fr.read(4),"little")
                        fr.seek(-4,1)
                        if lineTime < lastrun:
                            fr.seek(lineLength,1)
                            break
                        fr.seek(0,0) 
                        #reset to begining, because forward traversal is safer due to weird logger errors.
                        while 1:
                            findLineStart(fr)
                            lineTime = int.from_bytes(fr.read(4),"little")
                            fr.seek(1,1)
                            charlen = int.from_bytes(fr.read(1),"big")
                            fr.seek(charlen,1)
                            meslength = int.from_bytes(fr.read(2), "little")
                            fr.seek(meslength+2,1)
                            if lineTime > lastrun:
                                break
                        #backtrack when latest line is reached.
                        fr.seek(-2,1)
                        lineLength = int.from_bytes(fr.read(2),"little")+2
                        fr.seek(-lineLength,1)
                    findLineStart(fr)
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
                                # backwardsTraversalLength 2 bytes, little endian. Total length of all bytes in the line.
                                currentLine = logLine()
                                currentLine.setTime(lineTime)
                                debugvar = int.from_bytes(fr.read(1),"big")
                                currentLine.isAction(debugvar)
                                characterOffset = int.from_bytes(fr.read(1),"big")
                                character = (fr.read(characterOffset).decode("utf-8", "ignore"))
                                currentLine.setCharacter(character)
                                messageOffset = int.from_bytes(fr.read(2),"little")
                                message = fr.read(messageOffset).decode("utf-8", "ignore")
                                currentLine.setMessage(message)
                                fr.read(2) #Last 2 bytes for reverse traversal
                                if currentLine.character == "":
                                    break
                                currentLine.encodeLine()
                                fw.writelines(currentLine.encodedLine) 
                                #Fix for F-list occasionally leaving strings of 0x00 when the logger breaks.
                                # Improved fix is now logger mistake agnostic. It will seek until it finds a valid user name.
                                findLineStart(fr)
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
