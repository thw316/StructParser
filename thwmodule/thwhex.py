#import IntelHex
import time
import os

def InverBit(h):
    if type(h) is THWHex:
        for byteIdx in range(len(h)):
            num = h.GetVal(byteIdx)
            num = 0xFF ^ num
            h.SetVal(num, byteIdx)
        return h
    else:
        print("Please input THWHex type")



class THWHex(object):

    # private variable and functions

    __hexData = None

    def __Reduce2ByteList(self, lIn):
        lInLen = len(lIn)
        
        lInByteLen = 1
        maxVal = max(map(abs, lIn))
        while(maxVal>0xFF):
            maxVal >>= 8
            lInByteLen += 1

        if lInByteLen == 1:
            lOut = [lIn[lInIdx]&0xFF for lInIdx in range(lInLen)]
        else:
            lOut = [0] * lInLen * lInByteLen
            for lInIdx in range(lInLen):
                val = lIn[lInIdx]
                for byteIdx in range(lInByteLen):
                    lOut[lInIdx*lInByteLen + byteIdx] = val&0xFF
                    val >>= 8
        return lOut

    def __l2d(self, lIn):
        return {i: lIn[i] for i in range(len(lIn))}

    def __d2l(self, dIn, dummyPattern = 0xFF):
        keys = sorted(list(dIn.keys()))
        lOut = [0xFF] * (keys[-1]-keys[0]+1)
        for idx in range(len(lOut)):
            lOut[idx] = dIn[keys[idx]]
        return lOut

    def __intelhex2List(self, content, dummyPattern = 0xFF):
        content = content.split()
        
        extLinearAddr = "0000"
    
        maxAbsAddr = 0
        minAbsAddr = 0xFFFFFFFF

        for contentIdx in range(len(content)):
            if content[contentIdx][0] is not ':':
                raise SyntaxError("intel hex loss record mark : at line %d" % contentIdx)
            
            subContent = content[contentIdx][1:-2]
            checksum = content[contentIdx][-2:]
            dataLen = subContent[0:2]
            addr = subContent[2:6]
            types = subContent[6:8]
            data = subContent[8:]
        
            if types == "00":
                absAddr = int(extLinearAddr+addr, 16)
                if absAddr < minAbsAddr:
                    minAbsAddr = absAddr
                absAddr += (int(dataLen, 16)-1)
                if absAddr > maxAbsAddr:
                    maxAbsAddr = absAddr
            elif types == "01":
                break;
            #elif types == "02":
            #elif types == "03":
            elif types == "04":
                extLinearAddr = data
            #elif types == "05":
            else:
                raise SyntaxError("Unexpected intel hex record type %s" % types)

        print("maxAbsAddr 0x%08x, minAbsAddr 0x%08x" % (maxAbsAddr, minAbsAddr))

        lOut = [0xFF] * (maxAbsAddr - minAbsAddr + 1)

        for contentIdx in range(len(content)):
            if content[contentIdx][0] is not ':':
                raise SyntaxError("intel hex loss record mark : at line %d" % contentIdx)
            
            subContent = content[contentIdx][1:-2]
            checksum = content[contentIdx][-2:]
            dataLen = subContent[0:2]
            addr = subContent[2:6]
            types = subContent[6:8]
            data = subContent[8:]

            if types == "00":
                for byteIdx in range(int(dataLen, 16)):
                    strIdx = byteIdx<<1
                    lOut[int(extLinearAddr+addr, 16)+byteIdx-minAbsAddr] = int(data[strIdx:(strIdx+2)], 16) 
            elif types == "01":
                break;
            #elif types == "02":
            #elif types == "03":
            elif types == "04":
                extLinearAddr = data
            #elif types == "05":
            else:
                raise SyntaxError("Unexpected intel hex record type %s" % types)
    
        return lOut
        
    def __hexbin2List(self, inputFilePath):

        if inputFilePath.endswith(".hex"):
            readModeSearch = ["hex", "bin"]
        else:
            readModeSearch = ["bin", "hex"]

        fileSize = os.path.getsize(inputFilePath)
        readSize = 1*1024*1024*1024

        for readMode in readModeSearch:

            if readMode is "hex":
                mode = "r"
            else:
                mode = "rb"

            try:
                with open(inputFilePath, mode) as fp:
                    content = fp.read()
                    #content = "".join([fp.read(readSize) for idx in ([readSize]*((fileSize+readSize-1)//readSize))])
                    break
            except UnicodeDecodeError:
                if readMode is readModeSearch[-1]: # if last read mode still get Unicode Decode Error, then raise it.
                    raise

        if readMode is "hex":
            return self.__intelhex2List(content, 0xFF)
        else:
            return list(content)
        
    # public functions

    def __init__(self, src=None, offset=0, length=0, debug=0):
        
        if src is not None:
            srcType = type(src)
            if srcType is range:
                lSrc = list(src)
                lSrc = self.__Reduce2ByteList(lSrc)
            elif srcType is str: # file path
                if src.endswith(".txt"):
                    print("Read text file: "+src)
                    with open(src, 'r') as fp:
                        lSrc = list(map(lambda lString: int(lString, 16) ,fp.read().split()))
                        lSrc = self.__Reduce2ByteList(lSrc)
                else:
                    print("Read from file: "+src)
                    lSrc = self.__hexbin2List(src)
            elif srcType is THWHex:
                print("Read from another THWHex")
                lSrc = src.__hexData
            else:
                raise TypeError("Type of src only can be list or string of file path")

            if lSrc is not None:
                if offset and offset<len(lSrc):
                    lSrc = lSrc[offset:]
                if length and length<len(lSrc):
                    lSrc = lSrc[0:length]
                print("Truncate offset = 0x%08x, length=0x%08x" % (offset, len(lSrc)))

            self.__hexData = lSrc

    #def __repr__(self):
    #    self.Print()
    #    return "repr mapping to self.Print()"

    def __len__(self):
        return len(self.__hexData)

    def __call__(self, idx, byteLen=1):
        return self.GetVal(idx, byteLen)

    def __eq__(self, otherTHWHex):
        return self.__dict__ == otherTHWHex.__dict__

    def GetVal(self, idx, byteLen=1):
        if len(self) <= idx*byteLen:
            raise ValueError("idx and byteLen out of range, idx should be corresponding the byteLen")

        val = 0
        if byteLen == 1:
            val = self.__hexData[idx]
        else:
            for byteIdx in range(byteLen):
                val += self.__hexData[idx*byteLen + byteIdx] << (byteIdx<<3)

        return val

    def SetVal(self, value, idx, byteLen=1):
        if len(self) <= idx*byteLen:
            raise ValueError("idx and byteLen out of range, idx should be corresponding the byteLen")
        mask = int('FF'*byteLen, 16)
        value &= mask
        idx *= byteLen
        for byteIdx in range(byteLen):
            self.__hexData[idx+byteIdx] = (value >> (byteIdx<<3)) & 0xFF

    def Insert(self, srcTHWHex, offset=None):
        if type(srcTHWHex) is THWHex:
            if offset is None:
                self.__hexData += srcTHWHex.__hexData
            else:
                self.__hexData = self.__hexData[:offset] + srcTHWHex.__hexData + self.__hexData[offset:]
        else:
            print("Please input THWHex type")

    def WrFile(self, filePath, fileFormat=None):
        if self.__hexData == None:
            print("Nothing to write")
        else:
            if fileFormat is None:
                lastDotPos = filePath.rfind('.')
                if lastDotPos is -1:
                    fileFormat = "bin"
                else:
                    fileFormat = filePath[lastDotPos+1:]

            print("Write file: "+filePath+" , file extension: "+fileFormat)
            if fileFormat == "bin":
                with open(filePath, "wb") as fp:
                    fp.write(bytearray(self.__hexData))
            else:
                IntelHex(self.__l2d(self.__hexData)).tofile(filePath, format=fileFormat)

    def FillPattern(self, value, length=512, byteLen=1, increase=0, decrease=0):
        mask = int('FF'*byteLen, 16)
        value &= mask
        self.__hexData = [value] * length
        if increase:
            for idx in range(1, length):
                self.__hexData[idx] = (self.__hexData[idx-1]+1) & mask
        elif decrease:
            for idx in range(1, length):
                self.__hexData[idx] = (self.__hexData[idx-1]-1) & mask
        self.__hexData = self.__Reduce2ByteList(self.__hexData)

    def Print(self, byteLen=1, colPerRow=None, showOffset=1, showAscii=1, filePath=None, endian="little"):
        if self.__hexData is None:
            print("Nothing to print.")
            return

        if (colPerRow is None) or (colPerRow is 0):
            if byteLen <= 16:
                colPerRow = 16//byteLen
            else:
                colPerRow = 1
    
        formatSetting = "%0"+str(byteLen<<1)+"x "
    
        string = "" # initial
    
        if showOffset:
            #          _0x00000000__
            string += " Offset r\c  "
            for colIdx in range(colPerRow):
                string += formatSetting % (colIdx * byteLen)
            if showAscii:
                string += " Ascii"
            string += "\n"

        hexDataLan = len(self.__hexData)
        bytesPerRow = byteLen*colPerRow
        hexDataIdx = 0
        for rowIdx in range((hexDataLan+bytesPerRow-1)//bytesPerRow):
            if showOffset:
                string += " 0x%08x  " % hexDataIdx
            
            hexDataIdxBk = hexDataIdx
            for colIdx in range(colPerRow):
                colStr = ""
                for byteIdx in range(byteLen):
                    if hexDataIdx < hexDataLan:
                        if endian is "little":
                            colStr = "%02x" % self.__hexData[hexDataIdx] + colStr
                        else:
                            colStr = colStr + "%02x" % self.__hexData[hexDataIdx] 
                        hexDataIdx += 1
                    else:
                        colStr = "  " + colStr
                string += (colStr + " ")

            if showAscii:
                lAscii = list(map(chr, self.__hexData[hexDataIdxBk:(hexDataIdxBk+bytesPerRow)]))
                for idx in range(len(lAscii)):
                    if (lAscii[idx]<chr(32)) or (chr(126)<lAscii[idx]):
                        lAscii[idx] = "."
                string += (" "+"".join(lAscii))

            string += "\n"
    
        if filePath is None:
            print(string)
        else:
            f = open(filePath, 'w', encoding='utf-8')
            f.write(string)
            print("Write text file: %s" % filePath)
        
