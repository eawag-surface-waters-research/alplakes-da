#! /usr/bin/python2

'''A one dimensional pollution model. '''

import sys
import math
import os
import sys
import traceback

DEBUG = False

def dbg(msg):
    if DEBUG:
        print("[DEBUG]", msg, flush=True)

dbg("SCRIPT STARTED")
dbg(f"CWD = {os.getcwd()}")
dbg(f"ARGS = {sys.argv}")
dbg(f"EXECUTABLE PATH = {sys.executable}")


def defaultInput():
    input={}
    # grid
    input['x']= [0.0, 1.0, 4.0] 
    # stationary flow
    input['u'] = [1.0, 1.0, 1.0, 1.0, 1.0]
    # cross sectional area
    input['a'] = [1.0, 1.0, 1.0, 1.0, 1.0]
    # initial concentrations
    input['c'] = [0.1, 0.2, 0.3, 0.4, 0.5]
    # simulation timespan
    input['refdate'] = '01 dec 2000'
    #unit is always seconds
    input['unit'] = 'seconds'
    input['time'] = [0.0, 1.0, 10.0]
    # sources mass/m^3/s
    input['source_locations'] = [2]
    input['source_labels'] = ['default']
    input['source_values']= {}
    input['source_values']['default'] = [5.0]
    # boundaries
    input['bound_labels']=['left', 'right']
    input['bound_locations']=[0, -1]
    input['bound_values']={}
    input['bound_values']['left']=[-1000.0, 0.01, 0.02, 0.03]
    input['bound_values']['right']=[0.0]
    #output (index based and 0 based)
    input['output_file'] = 'default.output'
    input['output_locations'] = [1, 2]
    input['output_labels']=['defaultOutput1', 'defaultOutput2']
    return input

def initOutput(input):
    output={}
    #output (index based and 0 based)
    output['output_file'] = input['output_file']
    output['output_locations'] = input['output_locations']
    output['output_labels']=input['output_labels']
    output['output_values']={}
    for label in output['output_labels']:
        output['output_values'][label]=[]
    output['refdate']=input['refdate']
    output['unit']=input['unit']
    output['time']=input['time']
    return output

def computeNextTimeStep(tIndex, c, input):
    #print 'computing next timestep'
    cNext = [0.0 for dummy in c]
    #print 'c='+str(cNext)
    #print 'transport '
    time=input['time']
    x=input['x']
    u=input['u']
    for i in range(0, len(c), 1):
        #print 'computing for gridpoint '+str(i)
        di = u[i]*time[1]/x[1]
        iLeft = i+int(math.floor(di))
        #print 'i = %d di= %f iLeft = %f' % (i, di, iLeft)
        weightRight= (di-math.floor(di))
        weightLeft=1.0-weightRight
        iRight = iLeft+1
        if((iLeft>=0) & (iLeft<len(cNext))):
            cNext[iLeft]  +=  c[i]*weightLeft;
        if((iRight>=0) & (iRight<len(cNext))):
            cNext[iRight] += c[i]*weightRight
    #print 'c='+str(cNext)
    #print 'add sources'
    source_locations=input['source_locations']
    source_labels=input['source_labels']
    source_values=input['source_values']
    a=input['a']
    for iSource  in range(len(source_locations)):
        iLoc = source_locations[iSource]
        iLabel=source_labels[iSource]
        cValues = source_values[iLabel]
        if(tIndex<len(cValues)):
            cValue = cValues[tIndex]
        else:
            cValue = cValues[-1]
        cValue = max(cValue, 0.0)
        cNext[iLoc]+=cValue*time[1]/x[1]/a[iLoc]
    #print 'c='+str(cNext)
    #print 'inflow boundaries'
    bound_values=input['bound_values']
    if (u[0]>0.0):
        bValues=bound_values['left']
        if(tIndex<len(bValues)):
            bValue = bValues[tIndex]
        else:
            bValue = bValues[-1]
        bValue=max(bValue, 0.0)
        cNext[0] = bValue
    if (u[-1]<0.0):
        bValues=bound_values['right']
        if(tIndex<len(bValues)):
            bValue = bValues[tIndex]
        else:
            bValue = bValues[-1]
        cNext[-1]=bValue
    #print 'c='+str(cNext)
    return cNext

def readInputFile(fileName):
    dbg(f"readInputFile() called with: {fileName}")
    input = {
        "source_values": {},
        "bound_values": {},
        "output_values": {}
    }
    print('reading input from file '+fileName)
    dbg(f"Trying to open file: {fileName}")
    dbg(f"Absolute path: {os.path.abspath(fileName)}")
    dbg(f"Files in cwd: {os.listdir('.')}")
    try:
        inFile = open(fileName, 'r')
    except Exception as e:
        dbg(f"FAILED to open file: {e}")
        raise
    counter =1
    for line in inFile:
        #print "%d : %s" %(counter, line[:-1])
        if "=" in line and not line.strip().startswith("#"):
            dbg(f"EXEC LINE: {line.strip()}")
        exec(line, {}, input)
        counter+=1
    inFile.close()
    input['x'] = input['x']
    input['u'] = input['u']
    input['a'] = input['a']
    input['c'] = input['c']
    input['refdate'] = input['refdate']
    input['unit'] = input['unit']
    input['time'] = input['time']

    input['source_locations'] = input['source_locations']
    input['source_labels'] = input['source_labels']
    input['source_values'] = input['source_values']

    input['output_file'] = input['output_file']
    input['output_locations'] = input['output_locations']
    input['output_labels'] = input['output_labels']

    input['bound_labels'] = input['bound_labels']
    input['bound_locations'] = input['bound_locations']
    input['bound_values'] = input['bound_values']
    dbg(f"x = {input['x']}")
    dbg(f"u length = {len(input['u'])}")
    dbg(f"a length = {len(input['a'])}")
    dbg(f"c length = {len(input['c'])}")
    return input
    
def collectOutput(c, output):
    for i in range(len(output['output_locations'])):
        iOutput =output['output_locations'][i]
        iLabel=output['output_labels'][i]
        output['output_values'][iLabel].append(c[iOutput])
        #print 'c[%d]=%f' % (iOutput, c[iOutput])
    #print 'c='+str(c)

def writeOutput(output, c):
    outFile=open(output['output_file'], 'w')
    print("writing output to file %s" % output['output_file'])
    outFile.write("output_labels=["+','.join([ "'"+label+"'" for label in output['output_labels']])+"]\n")
    output_locations=output['output_locations']
    for i in range(len(output_locations)):
        if (output_locations[i]<0):
            output_locations[i] += len(output_locations)
    outFile.write("output_locations=["+','.join(map(str, output_locations[:]))+"]\n")
    output_values=output['output_values']
    for i in range(len(output_locations)):
        outFile.write("output_values['"+output['output_labels'][i]+"']=["+','.join(map(str, output_values[output['output_labels'][i]]))+"]\n")
    outFile.write("c=["+','.join(map(str, c))+"]\n")
    outFile.write("refdate='%s'\n"%output['refdate'])
    outFile.write("unit='%s'\n" % output['unit'])
    outFile.write("time=[%f,%f,%f] \n" %(output['time'][0],output['time'][1],output['time'][2])) 
    outFile.close()

def frange(start, end=None, inc=None):
    "A range function, that does accept float increments..."
    if end == None:
        end = start + 0.0
        start = 0.0
    if inc == None:
        inc = 1.0
    L = []
    while 1:
        next = start + len(L) * inc
        if inc > 0 and next >= end:
            break
        elif inc < 0 and next <= end:
            break
        L.append(next)        
    return L


if __name__ == '__main__':
    # look for input file
    input={}
    dbg("Checking input arguments")

    if len(sys.argv) > 1:
        inputFile = sys.argv[-1]
        dbg(f"Input file candidate = {inputFile}")
    else:
        inputFile = None
        dbg("No input file provided")

    if inputFile and inputFile.endswith(".input"):
        dbg("Reading input file")
        input = readInputFile(inputFile)
    else:
        dbg("Using default input")
        input = defaultInput()
    
    output=initOutput(input)
    print('main computations')
    tIndex = 0
    cNow=input['c'][:]
    time=input['time']
    collectOutput(cNow, output)
    for t in frange(time[0], time[2], time[1]):
        print('computing from time '+str(t)+' to '+str(t+time[1])+'  '+str(100*(t)/(time[2]-time[0]))+'%')
        cNow=computeNextTimeStep(tIndex, cNow, input)
        collectOutput(cNow, output)
        tIndex+=1
    writeOutput(output, cNow)
    print('simulation ended successfully')
