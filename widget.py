import termwin
from termwin import *

class Widget:
	@property
	def weight(s): return s._weight
	@property
	def height(s): return s._height
	@property
	def width(s): return s._width
	@property
	def column(s): return s._column
	@property
	def row(s): return s._row

	def __init__(s, weight=1, background='000000', foreground='ffffff'):
		s._column = 0
		s._row = 0
		s._height = 0
		s._width = 0
		s._weight = weight

		s._die = False
		s._new = True

		s.background = tuple(int(background[i:i+2], 16) for i in (0,2,4))
		s.foreground = tuple(int(foreground[i:i+2], 16) for i in (0,2,4))
		s.parent = None

	def die(s):
		s._die = True

	def resize(s, column, row, height, width):
		s._column = column
		s._row = row
		s._height = height
		s._width = width

	def _draw(s):
		raise Exception('Method must be ovewritten')

	def clear(s):
		with termwin._draw_lock:
			print(
					s._setcolors() + \
					termwin._move(
						s.column,
						s.row
						) + ''.join(
							[' ' * s.width + termwin._left(s.width - 1) + termwin._down()] * s.height) + \
						s._resetcolors(),
						end=''
						)

	def _setcolors(s):
		colors = '\033[48;2;{};{};{}m'.format(*s.background)
		colors += '\033[38;2;{};{};{}m'.format(*s.foreground)
		return colors

	def _resetcolors(s):
		return '\033[0m'
