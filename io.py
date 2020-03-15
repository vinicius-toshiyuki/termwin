import time
import fcntl
import struct
import termios
import sys
import os
import re

__old = None
__flags = None

class __output:
	def __init__(s):
		s.tabstop = 4
		s.deletable = 0

	def put(s, text):
		text = text.expandtabs(s.tabstop)
		if '\x02' in text:
			s.deletable = 0
			new = text#.replace('\x02', '')
		else:
			new = ''
			for c in text:
				if c == '\b' and s.deletable > 0:
					s.deletable -= 1
					new += '\b \b'
				elif c != '\b':
					s.deletable += 1
					new += c
		print(new, end='', flush=True)

output = __output()

def setraw():
	global __old, __flags
	__old = termios.tcgetattr(sys.stdin)
	new = termios.tcgetattr(sys.stdin)

	new[3] &= ~termios.ECHO
	new[3] &= ~termios.ICANON

	termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, new)

	__flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL) 
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, __flags | os.O_NONBLOCK) 

def unsetraw():
	__old[3] |= termios.ECHO
	__old[3] |= termios.ICANON
	termios.tcsetattr(sys.stdin, termios.TCSANOW, __old)
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, __flags)

def readchar():
	get = lambda: sys.stdin.buffer.raw.read(1)
	while not (c := get()):
		time.sleep(1/24)
	while True:
		try:
			c = c.decode()
			if c == '[' and get().decode() == 'C':
				c = '>'
			break
		except:
			c += get()
	return c

def read(prompt=None):
	s = ''
	if prompt:
		output.put(prompt+'\x02')
	while (c := readchar()) != '\n':
		if ord(c) == 127 or ord(c) == 8:
			s = s[:-1]
			c = '\b'
		else:
			s += c
		output.put(c)
	output.put('\n')
	return s

def write(text, end='\n'):
	output.put(text + end)

def gettermsize():
	st = struct.pack('HHHH', 0, 0, 0, 0)
	x = fcntl.ioctl(sys.stdout, termios.TGWINSZ, st)
	height, width = struct.unpack('HHHH', x)[:2]
	return (height, width)
