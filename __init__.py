import fcntl
import struct
import termios
import sys

from time import sleep
from threading import Thread, Condition, RLock

_draw_lock = RLock()

def gettermsize():
	st = struct.pack('HHHH', 0, 0, 0, 0)
	x = fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, st)
	height, width = struct.unpack('HHHH', x)[:2]
	return height, width

def _up(count=1):
	return '\033[{}A'.format(count)
def _down(count=1):
	return '\033[{}B'.format(count)
def _right(count=1):
	return '\033[{}C'.format(count)
def _left(count=1):
	return '\033[{}D'.format(count)

def _move(column, row):
	return '\033[{};{}H'.format(row, column)
 
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
