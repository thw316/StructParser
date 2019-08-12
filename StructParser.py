import csv
from module.thwhex import THWHex

def getValue(string):  # return string of Value name
    l = string.replace('<', '>').split('>')
    if (len(l) >= 2):
        return l[1]
    else:
        return string

# return [type name, type count], if type count ~= 0, it is an array
def getType(string):
    # Trans FlashFifo[255] to ['FlashFifo', '255', '']
    #  # get structName and structLens from [structName, structLens, '']
    l = string.replace('[', ']').split(']')[0:2]
    if (len(l) == 1) :
        return (l[0], 0)
    else:
        return (l[0], int(l[1]))

def getByteCnt(string):
    if (string == 'unsigned char'):
        return 1
    elif (string == 'unsigned short'):
        return 2
    elif (string == 'unsigned int'):
        return 4
    else:
        print("error getByteCnt")

def returnList(name, offset, bytecnt, arrlen):
    if type(name) is not str:
        print("error returnList name is not str")
    
    if type(offset) is not int:
        print("error returnList offset is not int")
    
    if type(bytecnt) is not int:
        print("error returnList bytecnt is not int")

    if type(arrlen) is not int:
        print("error returnList arrlen is not int")
    
    return [name, offset, bytecnt, arrlen]

def getHexByteLen(hexIIn, idx, byteLen):
    return '0x' + ''.join(['%02x' % hexIIn(idx+idxByte) for idxByte in reversed(range(byteLen))])

csvpath = 'test_StructParser\StructParser_BHFSVN36\garFlashFifoR.csv'

templist = ''
tmpArrLen = 0

structVarName = 'garFlashFifoR'
structName = ''
structLens = 0
structBaseAddr = 0xFFFFFFFF
structFormat = []
structSize = 0

with open(csvpath, newline='') as csvf:
    rows = csv.DictReader(csvf)
    for row in rows:

        if tmpArrLen != 0:
            tmpArrLen = tmpArrLen - 1
            continue

        elif (getValue(row['Value']) == 'array'):

            if (row['Expression'] == structVarName): # first line get struct info
                [structName, structLens] = getType(row['Type'])
                structBaseAddr = int(row['Location'], 16)
            else:
                tmpArrLen = getType(row['Type'])[1]
                templist = returnList(row['Expression'], int(row['Location'], 16)-structBaseAddr, getByteCnt(getType(row['Type'])[0]), tmpArrLen)

        elif (getValue(row['Value']) == 'struct'):
            
            if (getType(row['Type'])[0] == structName): # meet struct line again
                if (row['Expression'] == '[0]'): # second line
                    continue
                elif (row['Expression'] == '[1]'): # next element of struct array, end of parsing
                    structSize = int(row['Location'], 16) - structBaseAddr
                    break

        else:
            templist = returnList(row['Expression'], int(row['Location'], 16)-structBaseAddr, getByteCnt(getType(row['Type'])[0]), tmpArrLen)
        
        if templist:
            structFormat.append(templist)
            templist = ''

print(structName, structLens, structBaseAddr, structSize)

binpath = 'test_StructParser\StructParser_BHFSVN36\garFlashFifoR.hex'

binIn = THWHex(binpath)

with open(binpath+'.csv', 'w', newline='') as csvf:
    fieldnames = ['ptr', 'ptr(hex)']
    for l in structFormat:
        fieldnames.append(l[0])
    writer = csv.DictWriter(csvf, fieldnames=fieldnames)
    writer.writeheader()

    for idx in range(0,structLens):
        dic = {}
        dic = {'ptr': idx, 'ptr(hex)': hex(idx)}

        for l in structFormat:
            print(idx, l)
            if l[3]:
                dic[l[0]] = ','.join([getHexByteLen(binIn, idx*structSize+l[1]+idx2, l[2]) for idx2 in range(l[3])])
            else:
                dic[l[0]] = getHexByteLen(binIn, idx*structSize+l[1], l[2])

        print(dic)
        writer.writerow(dic)
        dic.clear()