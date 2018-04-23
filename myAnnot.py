#!/usr/bin/env python3

import os
import sys
import mmap
import json
from pprint import pprint
from subprocess import call

def seek_pre_char(filename, start, target):
	with open(filename, 'r') as f:
		i = 0
		tar = 0
		while(i<start):
			f.seek(i)
			if(f.read(1) == target):
				tar = i
			i = i+1
		return tar

def seek_aft_char(filename, start, target):
	with open(filename, 'r') as f:
		i = start
		tar = 0
		while(1):
			f.seek(i)
			if(f.read(1) == target):
				tar = i
				break
			i = i+1
		return tar

def nested_seek(filename, start, preaft, st):
	if(preaft == 0):
		i = start
		for s in st:
			i = seek_pre_char(filename, i, s)
		return i
	if(preaft == 1):
		i = start
		for s in st:
			i = seek_aft_char(filename, i, s)
		return i

def analyze(kay):
	print("We don't know anything right now. This is for using the string to determine things like type.")

def print_range(filename, start):
	i = nested_seek(filename, start, 0, ['{', '[', '{'])
	j = nested_seek(filename, start, 1, ['}', ']', '}'])
	print("%i, %i"%(i,j))
	with open(filename, 'r') as f:
		f.seek(i)
		k = json.loads(f.read(j-i+1))
		pprint(k)
		analyze(k)

def find_address():
	filename = 'out_%s'%(sys.argv[1])
	with open(filename, 'r') as f:
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		target = '%i'%int(sys.argv[2], 0)
		loc = s.find(target.encode())
		if loc != -1:
			print('true: %i, %s'%(loc, target))
			print_range(filename, loc)
			#j = json.loads(f.read())
			#pprint(j)	
		else:
			print('false')

def main():
	execute = '/home/matthew/Downloads/dynamorio/build/bin64/drrun -opt_cleancall 3 -c dynStruct -o out_%s -- tests/%s' % (sys.argv[1],sys.argv[1])
	print(execute);
	os.system(execute)
	find_address()

main()
