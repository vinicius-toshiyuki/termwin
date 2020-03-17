import fcntl
import struct
import termios
import sys
import os
import curses

from time import sleep
from threading import Thread, Condition, RLock

_draw_lock = RLock()

__old = None
__flags = None
def setraw():
	global __old, __flags
	__old = termios.tcgetattr(sys.stdin)
	new = termios.tcgetattr(sys.stdin)

	new[3] &= ~termios.ECHO
	new[3] &= ~termios.ICANON

	#stdscr = curses.initscr()
	#curses.curs_set(0)

	termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, new)

	__flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL) 
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, __flags | os.O_NONBLOCK) 

	print('\033[?25l', end='', flush=True)

def unsetraw():
	print('\033[?25h', end='', flush=True)

	__old[3] |= termios.ECHO
	__old[3] |= termios.ICANON
	#curses.curs_set(1)
	#curses.endwin()
	termios.tcsetattr(sys.stdin, termios.TCSANOW, __old)
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, __flags)

def gettermsize():
	st = struct.pack('HHHH', 0, 0, 0, 0)
	x = fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, st)
	height, width = struct.unpack('HHHH', x)[:2]
	return height, width

"""
class __output:
	def __init__(s):
		s.tabstop = 4
		s.deletable = 0

	def print(s, *objects, end='\n', sep=' '):
		if end is None:
			end = '\n'
		if sep is None:
			sep = ' '

		text = list(map(lambda x: str(x), objects))
		text = sep.join(text) + end
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

	def input(s, prompt=None):
		text = ''
		if prompt is not None:
			output.put(prompt+'\x02')

		while (c := readchar()) != '\n':
			if ord(c) == 127 or ord(c) == 8:
				text = text[:-1]
				c = '\b'
			else:
				text += c
			print(c, end='', flush=True)
		print()
		return text

output = __output()
"""

up = '\x1b[A'
down = '\x1b[B'
right = '\x1b[C'
left = '\x1b[D'
def readchar():
	get = lambda: sys.stdin.buffer.raw.read(1)
	while not (c := get()):
		sleep(1/24)
	while True:
		try:
			c = c.decode()
			if c == '[':
				c2 = get()
				if c2.decode() == 'A':
					c = up
				if c2.decode() == 'B':
					c = down
				if c2.decode() == 'C':
					c = right
				if c2.decode() == 'D':
					c = left
			break
		except:
			c += get()
	return c

def _up(count=1):
	return '\033[{}A'.format(count)
def _down(count=1):
	return '\033[{}B'.format(count)
def _right(count=1):
	return '\033[{}C'.format(count)
def _left(count=1):
	return '\033[{}D'.format(count)

def _move(column, row):
	return '\x1b[{};{}H'.format(row, column)
 
from termwin.frame import Frame
class Root(Frame):
	def __init__(s, column, row, height, width, orientation='vertical', background='000000', foreground='ffffff'):
		super().__init__(orientation=orientation, background=background, foreground=foreground)
		s._column = column
		s._row = row
		s._height = height
		s._width = width

class Manager:
	__instance = None
	def __init__(s, background='000000', foreground='ffffff'):
		if Manager.__instance is None:
			Manager.__instance = s
			height, width = gettermsize()
			#height = 25
			#width = 50

			s._root = Root(
					1, 1, height, width,
					orientation='vertical',
					background=background,
					foreground=foreground
					)

			print('\033[2J', end='', flush=True)
		else:
			raise Exception('Can only have one instance of Manager')

	def get_instance():
		return Manager.__instance

	def die(s):
		s.root.die()
		print('\033[2J\033[1;1H', end='', flush=True)

	@property
	def root(s): return s._root
