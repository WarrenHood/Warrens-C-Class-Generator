#!/usr/bin/python

# C++ Class Generator
# Coded by Warren Hood (Xx~MoX~xX)

import os
import sys

PTRSIZE = 4

type_suffix_multiplier = {
	"1" : ["int","uint","char","uchar"],
	"4" : ["vec","vector","matrix","Matrix"],
}

type_alias = {
	"BOOL" : ["bit","bool"],
	"BYTE" : ["byte"],
	"int16" : ["word"],
	"uint16" : ["uword"],
	"int32" : ["dword","int"],
	"uint32" : ["udword","uint"],
	"int64" : ["qword"],
	"Matrix" : ["matrix"],
	"vec" : ["vecotr"],
	"uint64" : ["uqword"]
}

absolute_sizes = {
	"1" : ["BOOL","BYTE","char","uchar","bool"],
	"4" : ["int","uint","float","ufloat"],
	"8" : ["double","udouble"]
}

knownPrefixesAndTypes = [
	"BOOL",
	"BYTE",
	"char",
	"uchar",
	"int",
	"uint",
	"vec",
	"vector",
	"matrix",
	"Matrix"
]

def parseNumeric(numericString):
	try:
		return int(numericString)
	except:
		return int(numericString,16)

def getNumericalSuffix(typeName):
	for charIndex in range(len(typeName)):
		if typeName[charIndex].isnumeric() and len(typeName[charIndex:].replace("*","")):
			return int(typeName[charIndex:].replace("*",""))
	return -1

def sGetNumericalSuffix(typeName):
	for charIndex in range(len(typeName)):
		if typeName[charIndex].isnumeric() and len(typeName[charIndex:].replace("*","")):
			return str(typeName[charIndex:].replace("*",""))
	return "-1"

def getProperType(typeName):
	global type_alias
	for possibleType in type_alias.keys():
		if typeName in type_alias[possibleType]:
			return possibleType
	if "*" in typeName:
		baseName = typeName.replace("*","")
		for possibleType in type_alias.keys():
			if baseName in type_alias[possibleType]:
				return typeName.replace(baseName,possibleType)
	return typeName

def getAbsoluteSize(typeName):
	global absolute_sizes
	for typeSize in absolute_sizes.keys():
		if typeName in absolute_sizes[typeSize]:
			return int(typeSize)
	return -1

def getCPPTypeName(typeName):
	if getSuffixlessType(typeName) in ["int","uint","char","uchar"]:
		if sGetNumericalSuffix(typeName) != "-1":
			return typeName.replace(typeName.replace("*",""),typeName.replace("*","")+"_t")
	return typeName



def getSuffixlessType(typeName):
	for charIndex in range(len(typeName)):
		if typeName[charIndex].isnumeric():
			return typeName[:charIndex]
	return typeName

def isPointerType(typeName):
	return "*" in typeName


def getSuffixMultipler(typePrefix):
	global type_suffix_multiplier
	for size in type_suffix_multiplier.keys():
		if typePrefix in type_suffix_multiplier[size]:
			return int(size)
	input("An error has occurred with suffix multipliers!")
	sys.exit(0)

def getArrayLen(arrayName):
	if "[" not in arrayName:
		return 1
	currentLen = 1
	currentInside = ""
	bIsIndside = False
	for char in arrayName:
		if char == "[":
			if bIsIndside:
				input("Syntax error: " + arrayName)
				sys.exit(0)
			bIsIndside = True
			continue
		if char == "]":
			if not bIsIndside:
				input("Syntax error: " + arrayName)
				sys.exit(0)
			bIsIndside = False
			currentLen *= int(currentInside)
			currentInside = ""
			continue
		if bIsIndside:
			if char.isnumeric():
				currentInside += char
			else:
				input("Syntax error: Size of array not specified :",arrayName)
				sys.exit(0)
	return currentLen


def matrixSize(matrixSuffix):
	dimensions = list(map(int,matrixSuffix.lower().split("x")))
	return dimensions[0]*dimensions[1]*getSuffixMultipler("matrix")

def stripComments(line):
	for i in range(len(line)-1):
		if line[i] == "/" and line[i+1] == "/":
			return line[:i].strip()
	return line.strip()

def generateClass(arrayOfLines):
	global PTRSIZE
	global knownPrefixesAndTypes
	className = ""
	output = []
	for line in arrayOfLines:
		line = stripComments(line)
		if len(line) == 0:
			continue
		if line[0] == "#":
			className = line.replace("#","").strip()
			continue
		splitLine = line.split()
		thisType = getProperType(splitLine[0])
		cppType = getCPPTypeName(thisType)
		thisName = splitLine[1]
		thisOffset = parseNumeric(splitLine[2])

		#Pointer types (SIZE is always PTRSIZE)
		if isPointerType(thisType):
			output.append((thisOffset,cppType + " " + thisName + "; //" + hex(thisOffset).upper(),PTRSIZE*getArrayLen(thisName)))
			continue
		
		# Custom types 
		if ("x" not in sGetNumericalSuffix(thisType).lower()) and getSuffixlessType(thisType) not in knownPrefixesAndTypes:
			output.append((thisOffset,getSuffixlessType(thisType) + " " + thisName + "; //" + hex(thisOffset).upper(),getNumericalSuffix(thisType)*getArrayLen(thisName)))
			continue

		#Suffixed types
		if sGetNumericalSuffix(thisType) != "-1":
			# Matrix type
			if getSuffixlessType(thisType).lower() == "matrix":
				output.append((thisOffset,thisType + " " + thisName + "; //" + hex(thisOffset).upper(),matrixSize(thisType.replace(getSuffixlessType(thisType),""))*getArrayLen(thisName)))
				continue
			# Vector type
			if getSuffixlessType(thisType) in ["vec","vector"]:
				output.append((thisOffset,thisType + " " + thisName + "; //" + hex(thisOffset).upper(), getNumericalSuffix(thisType)*getSuffixMultipler("vec")*getArrayLen(thisName)))
				continue
			# One of the int, uint , char, uchar suffixed types
			output.append((thisOffset,cppType + " " + thisName + "; //" + hex(thisOffset).upper(),int(getNumericalSuffix(thisType)*getArrayLen(thisName)/8)))
			continue

		# One of the "absolute" types
		output.append((thisOffset,thisType + " " + thisName + "; //" + hex(thisOffset).upper(), getAbsoluteSize(thisType)*getArrayLen(thisName)))
	output.sort()


	currentOffset = 0
	print("class "+className+"{\npublic:")
	for line in output:
		if currentOffset < line[0]:
			print("    char pad_" + hex(line[0]).replace("0x","").upper() + "[" + str(line[0]-currentOffset) + "]; //" + hex(currentOffset).upper())
			currentOffset = line[0]
		print(" "*4 + line[1])
		currentOffset += line[2]
		#print("Size = " + hex(line[2]))
	print("}; // Size = "+hex(currentOffset).upper() + "// Generated by Warren Hood's C++ Class Generator")
	print()

def genClasses(source):
	global PTRSIZE
	sourceLines = source.split('\n')
	currentSource = []
	bInSource = False
	for line in sourceLines:
		line = line.strip()
		if len(line) == 0:
			continue
		if not bInSource:
			if line[0] == "#":
				bInSource = True
				currentSource.append(line)
				continue
			if "PTRSIZE" in line and line[:7] == "PTRSIZE":
				if len(line.split()) < 2:
					input("Syntax error: Expected value of PTRSIZE but none given")
					sys.exit(0)
				try:
					PTRSIZE = int(line.split()[1])
				except:
					input("Syntax error: "+line)
					sys.exit(0)
		else:
			if line[0] == "#":
				generateClass(currentSource)
				currentSource.clear()
			currentSource.append(line)
	generateClass(currentSource)

if len(sys.argv) == 2:
	sourcefile = open(sys.argv[1],"r")
	genClasses(sourcefile.read())
	sourcefile.close()
	input()
else:
	sourcefile = open(input("Enter filename or path to file: "),"r")
	os.system("CLS")
	genClasses(sourcefile.read())
	sourcefile.close()
	input()
