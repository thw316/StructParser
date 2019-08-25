import csv
from os import listdir
from thwmodule.thwhex import THWHex
# Settings
configfolder = 'config'

#function
# getValue return string
def getValue(string):  # return string of Value name
    return string.replace('<', '').replace('>', '').split('"')[0]

# getTpye return [type name, array lens] for array. return [type name] for single value.
def getType(string):
    lOut = string.replace(']','').split('[')
    return [lOut[0]] + list(map(int, lOut[1:]))

# getByteCnt return byte count
def getByteCnt(string):
    if (string == 'unsigned char'):
        return 1
    elif (string == 'unsigned short'):
        return 2
    elif (string == 'unsigned int'):
        return 4
    else:
        print("error getByteCnt")
        exit(1)

# define list
def returnList(name, offset, bytecnt, arrlen):
    if type(name) is not str:
        print("error returnList name is not str")
        exit(1)
    
    if type(offset) is not int:
        print("error returnList offset is not int")
        exit(1)
    
    if type(bytecnt) is not int:
        print("error returnList bytecnt is not int")
        exit(1)

    if type(arrlen) is not list:
        print("error returnList arrlen is not int")
        exit(1)
    
    return [name, offset, bytecnt, arrlen]

# return hex value from dynamic offset with byte count
def getHexByteLen(hexIIn, idx, byteLen):
    return '0x' + ''.join(['%02x' % hexIIn(idx+idxByte) for idxByte in reversed(range(byteLen))])

def multiplyList(myList) : 
    # Multiply elements one by one 
    result = 1
    for x in myList: 
         result = result * x  
    return result

def listDim2StrDim(lIn):
    string = ''
    for e in lIn:
        string = string + '[%s]' % (str(e))
    return string

# main
if __name__ == '__main__':

    while True:
        # handle input
        binPath = input("Input binary path (.bin/.hex): ")
        print("")
        
        configNames = listdir(configfolder)
        print ("0: load other config")
        for i in range(len(configNames)):
            print ("%d: %s" % (i+1, configNames[i]))

        i = int(input("Select above config file: "))

        if (0<i) and (i<=len(configNames)): # select from configfolder
            cfgfile = '%s/%s' % (configfolder, configNames[i-1])
        else:
            cfgfile = input("Input config path: ")

        print ("Load config file: %s" % cfgfile)
        print("")

        # struct var
        structVarName = '' # get from first row
        structName = '' # get from first row
        structLens = 0 # get from first row
        structBaseAddr = 0xFFFFFFFF # get from first row

        structFormat = [] # main format

        structSize = 0 # get from struct[1] addr - struct[0] addr

        with open(cfgfile, 'r', newline='', encoding='utf-8') as csvf:

            rows = csv.DictReader(csvf)

            stage = 1
            for row in rows:

                if stage == 1: # found array of structs (AoS)
                    if getValue(row['Value']) == 'array': # get info of AoS
                        structVarName = row['Expression']
                        structBaseAddr = int(row['Location'], 16)
                        tempList = getType(row['Type'])
                        if len(tempList) != 2:
                            print("error array of struct not support")
                            exit(1)
                        structName = tempList[0]
                        structLens = tempList[1]
                        stage = 2

                elif stage == 2: # found first element of AoS
                    if (getValue(row['Value']) == 'struct'):
                        if (row['Expression'] == '[0]') and (int(row['Location'],16) == structBaseAddr) and (getType(row['Type']) == [structName]):
                            stage = 3

                elif stage == 3: # construct structFormat
                    if (getValue(row['Value']) == 'struct'):
                        if (row['Expression'] == '[1]') and (getType(row['Type']) == [structName]): # found second element of AoS
                            structSize = int(row['Location'], 16) - structBaseAddr
                            break # break rows loop to complete config parsing
                        #else:
                            # do nothing... need user expand struct inside AoS
                    elif (getValue(row['Value']) == 'array'):
                        tempList = getType(row['Type'])
                        arrType = tempList[0]
                        arrLens = tempList[1:]
                        structFormat.append(returnList(row['Expression']+listDim2StrDim(arrLens), int(row['Location'], 16)-structBaseAddr, getByteCnt(arrType), arrLens))
                    elif ('[' not in row['Expression']):
                        structFormat.append(returnList(row['Expression'], int(row['Location'], 16)-structBaseAddr, getByteCnt(getType(row['Type'])[0]), [1]))

        print("Name: %s, Lens: %s, Base Addr: %s, Size %s" % (structName, structLens, structBaseAddr, structSize))
        print("Struct format: [name, offset, byte cnt, array lens]")
        for l in structFormat:
            print(l)
        print("")

        binIn = THWHex(binPath)

        with open(binPath+'.csv', 'w', newline='', encoding='utf-8') as csvf:
            fieldnames = ['ptr', 'ptr(hex)']
            for l in structFormat:
                fieldnames.append(l[0])
            writer = csv.DictWriter(csvf, fieldnames=fieldnames)
            writer.writeheader()

            for idx in range(0,structLens):
                dic = {}
                dic = {'ptr': idx, 'ptr(hex)': hex(idx)}

                for l in structFormat:
                    if l[3] != [1]:
                        dic[l[0]] = ','.join([getHexByteLen(binIn, idx*structSize+l[1]+idx2, l[2]) for idx2 in range(multiplyList(l[3]))])
                    else:
                        dic[l[0]] = getHexByteLen(binIn, idx*structSize+l[1], l[2])

                # print(dic)
                writer.writerow(dic)
                dic.clear()

        print("Parsing finish....")
        print("")
