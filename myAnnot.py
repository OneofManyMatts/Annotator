#!/usr/bin/env python3

import os
import sys
import mmap
import json
import re
from pprint import pprint
from subprocess import call

def seek_pre_char(filename, start, target, opposite):
	with open(filename, 'r') as f:
		i = start
		tar = 0
		count = 0
		while(i>0):
			f.seek(i)
			red = f.read(1)
			if(red == target):
				if(count == 0):
					tar = i
					break
				else:
					count = count - 1
			if(red == opposite):
				count = count + 1
			i = i-1
		return tar

def seek_aft_char(filename, start, target, opposite):
	with open(filename, 'r') as f:
		i = start
		tar = 0
		count = 0
		while(1):
			f.seek(i)
			red = f.read(1)
			if(red == target):
				if(count == 0):
					tar = i
					break
				else:
					count = count - 1
			if(red == opposite):
				count = count + 1
			i = i+1
		return tar

def nested_seek(filename, start, preaft, st):
	if(preaft == 0):
		i = start
		for s in st:
			if (s == '{'):
				i = seek_pre_char(filename, i, '{', '}')
			if (s == '['):
				i = seek_pre_char(filename, i, '[', ']')
		return i
	if(preaft == 1):
		i = start
		for s in st:
			if (s == '}'):
				i = seek_aft_char(filename, i, '}', '{')
			if (s == ']'):
				i = seek_aft_char(filename, i, ']', '[')
		return i


def size_analyze(ray):
	options = {	
		0 : 'This is a strange result indeed, and probably incorrect.',
		1 : 'This is likely either a binary value, a bool, or a char.',
		2 : 'A tiny array or a short int. Certain other ints can fit in two bytes as well, but in neraly all cases they will be 4 bytes.',
                4 : 'An int, long, float, or short array of one of the smaller types.',
		8 : 'This size, 8 bytes, is where it really starts getting ambiguous. Doubles are this size, but arrays of smaller types can fit in 8 bits.',
		10 : '10 bytes is the base size of a long double, so unless this is an array or a struct it\'s almost certainly a long double.'
	}
	if ray not in options:
		if(ray>10):
			print('Anything larger than 10 bytes was probably a chunk of data set aside for an array or other structure.')
		else:
			print('The strange allocation size makes it pretty clear this is a unique setup, a struct, or some mistake.')
	else:
		print(options[ray])

def opcode_analyze(op):
	options = {
		'8b00' : 'mov (%rax),%eax : This is an assignment, likely of four bytes or less.'
	}
	if op not in options:
		print('That opcode is not implemented.')
	else:
		print(options[op])

def analyze(kay):
	#print(kay)
	#include options for  'alloc_func','alloc_pc','end','free_func','free_pc', others
	if('size_access' in kay):
		m = re.search('\"size_access\":(\d+)', kay)
		j = m.group(1)
		print('Found Size Access Value: %s'%j)
		k = int(j, 0)
		size_analyze(k)
	if('opcode' in kay):
		m = re.search('\"opcode\":\"([0-9a-f]+)\"', kay)
		j = m.group(1)
		print('Found Opcode: %s'%j)
		r = '%s'%j
		opcode_analyze(r)
	print("We don't know everything right now. This is for using the string to determine things like type.")

def print_range(filename, start):
	i = nested_seek(filename, start, 0, ['{'])
	j = nested_seek(filename, start, 1, ['}'])
	print("%i, %i"%(i,j))
	with open(filename, 'r') as f:
		f.seek(i)
		r = f.read(j-i+1)
		k = json.loads(r)
		pprint(k)
		#k = f.read(j-i+1)
		#print(k)
		analyze(r)

def find_address():
	filename = 'out_%s'%(sys.argv[1])
	with open(filename, 'r') as f:
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		target = '%i'%int(sys.argv[2], 0)
		loc = 0
		loc = s.find(target.encode())
		foundloc = []
		while loc >= 0:
        		foundloc.append(loc)
        		loc = s.find(target.encode(), loc + 1)
		for found in foundloc:
			print('Found: %i, %s'%(found, target))
			print_range(filename, found)
			#j = json.loads(f.read())
			#pprint(j)	
		if(len(foundloc)<1):
			print('No matches found.')

def main():
	execute = '/home/matthew/Downloads/dynamorio/build/bin64/drrun -opt_cleancall 3 -c dynStruct -o out_%s -- tests/%s' % (sys.argv[1],sys.argv[1])
	print(execute);
	os.system(execute)
	find_address()

main()
