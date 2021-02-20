import sys, os
pwd = os.path.dirname(os.path.realpath(__file__))+"\\"
sys.path.append(pwd)

import csv
from module.thwhex import THWHex

# return byte count of types
getByteCnt = { 
        'unsigned char': 1,
        'unsigned short': 2,
        'unsigned int': 4,
        'unsigned int *': 4,
        'unsigned long long': 8
        }

# return string of Value name
def parsingvalue(string):

    if 'array' in string:
        return 'array'
    elif 'struct' in string:
        return 'struct'
    elif 'union' in string:
        return 'union'
    else:
        return 'others'

# getTpye return [type name, array lens] for array. return [type name, 1] for single value.
def parsingtype(string):

    if '[' in string:
        string = string.replace('[', '^').replace(']','^').split('^')
        typ = string[0]
        arrlen = int(string[1])
        return [typ, arrlen]
    else:
        return [string, 1]


# return hex value from dynamic offset with byte count
def getHexByteLen(hexIIn, idx, byteLen):
    return '0x' + ''.join(['%02X' % hexIIn(idx+idxByte) for idxByte in reversed(range(byteLen))])

def main():

    # handle input
    cfgFolder = None
    ifPath = None
    if len(sys.argv) >= 2:
        cfgFolder = sys.argv[1]
    if len(sys.argv) >= 3:
        ifPath = sys.argv[2]
    if len(sys.argv) > 3:
        raise ValueError("[cfg folder] [binary path]")
    if None == cfgFolder:
        cfgFolder = input("Input config folder")
    if None == ifPath:
        ifPath = input("Input binary path (.bin/.hex): ")

    ifTHWHex = THWHex(ifPath)
    cfgName = os.listdir(cfgFolder)
    print ("00: load other config")
    for cfgNameIdx in range(len(cfgName)):
        print ("%02d: %s" % (cfgNameIdx+1, cfgName[cfgNameIdx]))

    cfgNameIdx = int(input("Select above config file: "))

    if (0<cfgNameIdx) and (cfgNameIdx<=len(cfgName)): # select from cfgFolder
        cfgfile = '%s/%s' % (cfgFolder, cfgName[cfgNameIdx-1])
    else:
        cfgfile = input("Input config path: ")
    print("")

    # struct var
    structVarName = '' # get from first row
    structName = '' # get from first row
    structLens = 0 # get from first row
    structBaseAddr = 0xFFFFFFFF # get from first row

    structFormat = [] # main format

    structSize = 0 # get from struct[1] addr - struct[0] addr

    print("Loading %s" % cfgfile)
    with open(cfgfile, 'r', newline='', errors='replace') as csvf:

        if cfgfile.endswith(".log"):
            rows = csv.DictReader(csvf, delimiter='\t')
        else:
            rows = csv.DictReader(csvf)

        stage = 1
        for row in rows:

            exp = row['Expression']
            val = parsingvalue(row['Value'])
            loc = int(row['Location'], 16)
            [typ, arrlen] = parsingtype(row['Type'])

            #print(row)
            #print(exp, val, loc, typ, arrlen)

            if stage == 1: # found array of structs (AoS)
                if 'array' == val: # get info of AoS
                    structVarName = exp
                    structBaseAddr = loc
                    structName = typ
                    structLens = arrlen
                    stage = 2

            elif stage == 2: # found first element of AoS
                if '[0]' == exp and loc == structBaseAddr and typ == structName:
                        stage = 3

            elif stage == 3: # construct structFormat

                if 'union' in typ:
                    continue

                if typ not in getByteCnt:
                    if 'struct' in val:
                        if '[1]' == exp and typ == structName: # found second element of AoS
                            structSize = loc - structBaseAddr
                            break # break rows loop to complete config parsing
                        else:
                            continue # do nothing... need user expand struct inside AoS
                    else:
                        userinput = input("Type %s not defined, please enter its byte count: " % (typ))
                        if userinput == "":
                            print("Ignore this.")
                            continue
                        else:
                            getByteCnt[typ] = int(userinput)                            

                if arrlen == 1:
                    structFormat.append([exp, loc-structBaseAddr, getByteCnt[typ], 1])
                else:
                    structFormat.append(["%s[%s]" % (exp, arrlen), loc-structBaseAddr, getByteCnt[typ], arrlen])

    print("Name: %s, Lens: %s, Base Addr: 0x%08X, Size 0x%08X" % (structName, structLens, structBaseAddr, structSize))
    print("Struct format: [name, offset, byte cnt, array lens]")
    for l in structFormat:
        print(l)
    print("")

    ofName = ifPath+'.csv'
    print("Parsing to %s" % ofName)
    with open(ofName, 'w', newline='', encoding='utf-8') as csvf:
        fieldnames = ['ptr', 'ptr(hex)']
        for l in structFormat:
            fieldnames.append(l[0])
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()

        for idx in range(0,structLens):
            dic = {}
            dic = {'ptr': idx, 'ptr(hex)': "0x%02X" % idx}

            for l in structFormat:
                # print(idx, l)
                if l[3] == 1:
                    dic[l[0]] = getHexByteLen(ifTHWHex, idx*structSize+l[1], l[2])
                else:
                    dic[l[0]] = ','.join([getHexByteLen(ifTHWHex, idx*structSize+l[1]+idx2*l[2], l[2]) for idx2 in range(l[3])])

            # print(dic)
            writer.writerow(dic)
            dic.clear()

    input("Finish! Press any key to exit....")


# main
if __name__ == '__main__':

    try:
        main()
    except:
        from traceback import format_exc
        print(format_exc())
        input("Exit with error! Press any key to exit...")
