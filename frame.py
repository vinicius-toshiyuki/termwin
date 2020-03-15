import termwin
from termwin.widget import Widget

class Frame(Widget):
	def __init__(s, weight=1, background='000000', foreground='ffffff', orientation='vertical'):
		super().__init__(weight, background, foreground)

		s._orientation = orientation
		s._widgets = []
	
	def die(s):
		for w in s._widgets:
			w.die()
		super().die()

	# TODO: tem que arrumar os negócio de spare -> pode dar mais de um de spare?
	def resize(s, column, row, height, width):
		s._column = column
		s._row = row
		s._height = height
		s._width = width

		weight = sum([w.weight for w in s._widgets]) # peso total de todos os widgets
		if weight == 0:
			wheight = s._height
			wwidth = s._width
		elif s.orientation == 'vertical':
			wheight = (s._height - len(s._widgets) + 1) // weight # altura de cada peso de widget
			wwidth = s._width
			spare = (s._height - len(s._widgets) + 1) % weight
		elif s.orientation == 'horizontal':
			wheight = s._height
			wwidth = (s._width - len(s._widgets) + 1) // weight # largura de cada peso de widget
			spare = (s._width - len(s._widgets) + 1)  % weight

		roffset, coffset = 0, 0
		s.clear()
		for w in s._widgets:
			if s.orientation == 'vertical':
				w.resize(
						s._column + coffset,
						s._row + roffset,
						wheight * w.weight + (1 if spare > 0 else 0),
						wwidth
						)
				roffset += wheight * w.weight + (2 if spare > 0 else 1)
			elif s.orientation == 'horizontal':
				w.resize(
						s._column + coffset,
						s._row + roffset,
						wheight,
						wwidth * w.weight + (1 if spare > 0 and w != s._widgets[-1] else 0)
						)
				coffset += wwidth * w.weight + (2 if spare > 0 and w != s._widgets[-1] else 1)
			spare -= 1
		s._draw()

	@property
	def orientation(s): return s._orientation

	def addwidget(s, widget):
		s._widgets.append(widget)
		widget.parent = s
		s.resize(s._column, s._row, s._height, s._width)

	def _draw(s):
		with termwin._draw_lock:
			print(s._setcolors(), end='')
			for w in s._widgets:
				if s.orientation == 'vertical' and w != s._widgets[-1]:
					move = termwin._move(w.column, w.row + w.height)
					print(move + '─' * s._width, end='', flush=True)
				elif s.orientation == 'horizontal' and w != s._widgets[-1]:
					move = termwin._move(w.column + w.width, w.row)
					print(move + ('│' + termwin._left() + termwin._down()) * s._height, end='', flush=True)
			print(s._resetcolors(), end='')
