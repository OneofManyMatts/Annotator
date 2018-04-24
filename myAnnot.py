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
	load_assign_set ={
		'40' : '(%rax),%rax',
		'58' : '(%rax),%rbx',
		'48' : '(%rax),%rcx',
		'50' : '(%rax),%rdx',
		'43' : '(%rbx),%rax',
		'5b' : '(%rbx),%rbx',
		'4b' : '(%rbx),%rcx',
		'53' : '(%rbx),%rdx',
		'41' : '(%rcx),%rax',
		'59' : '(%rcx),%rbx',
		'49' : '(%rcx),%rcx',
		'51' : '(%rcx),%rdx',
		'42' : '(%rdx),%rax',
		'5a' : '(%rdx),%rbx',
		'4a' : '(%rdx),%rcx',
		'52' : '(%rdx),%rdx'
	}
	eightb_eightnine_ends = {
		'00' : '%eax',
		'18' : '%ebx',
		'08' : '%ecx',
		'10' : '%edx'
	}
	if(op[:2]=='48'):
		srh = op[0:6]+'(\\d+)'
		m = re.search(srh, op)
		j = m.group(1)
		if(op[2:4]=='8b'):
			a = load_assign_set[op[4:6]]
			print('mov 0x'+j+a+': Loading a value for use.')
			return 1
		if(op[2:4]=='89'):
			a = load_assign_set[op[4:6]][-4:]
			b = load_assign_set[op[4:6]][0:6]
			print('mov '+a+',0x'+j+b+': Assigning a value to the struct.')
			return 2
	elif(op[:2]=='8b'):
			print('mov (%rax),'+eightb_eightnine_ends[op[2:4]]+': This is a read from the structure as a whole.')
			return 3
	elif(op[:2]=='89'):
			print('mov '+eightb_eightnine_ends[op[2:4]]+',(%rax): This is an assignment to the structure as a whole')
			return 4
	else:
		print('Opcode not interpreted.')
		return -1

def alloc_free_analyze(kay, op):
	setofvals = {
		'alloc_func': 'This is the address of the start of the function where the structure was allocated.',
		'alloc_pc': 'This is the actual point in code where the structure was allocated.',
		'end': 'This is the end of where the structure is held in memory.',
		'free_func': 'This is the address of the start of the function where the structure was freed.',
		'free_pc': 'This is the actual point in code where the structure was freed.',
		'start': 'This is the start of where the structure is held in memory.',
	}
	for val in setofvals:
		if(val in kay):
			srh = '\"%s\":(\d+)'%val
			m = re.search(srh, kay)
			j = m.group(1)
			if(int(j, 0)==int(op, 0)):
				print(setofvals[val])
				return 1
	return -1

def analyze(kay, address):
	if(alloc_free_analyze(kay, address)<0):
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
	else:
		print('This address is in a struct. Details on the values written and read from it are given below in JSON.')

def print_range(filename, start, subject):
	i = nested_seek(filename, start, 0, ['{'])
	j = nested_seek(filename, start, 1, ['}'])
	#print("%i, %i"%(i,j))
	with open(filename, 'r') as f:
		f.seek(i)
		r = f.read(j-i+1)
		k = json.loads(r)
		analyze(r, subject)
		pprint(k)

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
			#print('Found: %i, %s'%(found, target))
			print_range(filename, found, target)	
		if(len(foundloc)<1):
			print('No matches found.')
		f.close()

def average_size():
	filename = 'out_%s'%(sys.argv[1])
	with open(filename, 'r') as f:
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		target = '"size":'
		loc = 0
		loc = s.find(target.encode())
		foundloc = []
		while loc >= 0:
        		foundloc.append(loc)
        		loc = s.find(target.encode(), loc + 1)
		str_num = 0 #struct number
		tot_siz = 0 #total struct size
		for found in foundloc:
			str_num = str_num+1
			f.seek(found)
			i = 7
			while(1):
				f.seek(found+i)
				r = f.read(1)
				if(r==','):
					break
				i = i+1
			f.seek(found+7)
			result = f.read(i-7)
			tot_siz = tot_siz + int(result, 0)
		if(len(foundloc)<1):
			print('No structs found.')
		else:
			average = tot_siz / str_num
			print('Average struct size is: %i.'%average)
		f.close()

def main():
	execute = '/home/matthew/Downloads/dynamorio/build/bin64/drrun -opt_cleancall 3 -c dynStruct -o out_%s -- tests/%s' % (sys.argv[1],sys.argv[1])
	print(execute);
	os.system(execute)
	average_size()
	find_address()

main()
