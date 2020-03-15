import re
import time
from threading import Thread, Condition
import termwin
from termwin.widget import Widget

class Window(Widget):
	tabstop = 4

	def __init__(s, weight=1, background='000000', foreground='ffffff', timeout=0, maxlines=100):
		super().__init__(weight, background, foreground)

		s.timeout = timeout
		s._max = maxlines

		s._ready = True
		s._idx = 0
		s._offset = 0
		s._content = []
		s._bs = False

		s.clear()
		s._draw_cond = Condition()
		s._timeout_cond = Condition()
		
		s._drawer = Thread(target=s._draw)
		with s._draw_cond:
			s._drawer.start()
			s._draw_cond.wait()


	def die(s):
		s._die = True
		with s._timeout_cond:
			s._timeout_cond.notify()
		with s._draw_cond:
			s._draw_cond.notify_all()
		s._drawer.join()

	def resize(s, column, row, height, width):
		super().resize(column, row, height, width)
		with s._draw_cond:
			s._idx = max(len(s._content) - height, 0)
			s._draw_cond.notify()
		s.clear()

	def wipe(s):
		with s._draw_cond:
			s._offset = 0
			s._idx = 0
			s._content = []
		s.clear()

	def _wraptext(s, text):
		return tuple(text[i:i+s.width] for i in range(0, len(text), s.width))

	def _format(s, text):
		text = text.expandtabs(Window.tabstop)
		prompt = text.rsplit('\x02', 1)
		if len(prompt) > 1:
			text = prompt[1]
			prompt = prompt[0] + '\x02'
		else:
			prompt = ''
		while '\b' in text:
			text = re.sub(r'^[\b]+', '', text)
			text = re.sub(r'[^\b][\b]', '', text)
		return prompt + text

	def put(s, text):
		s._draw_cond.acquire()

	 	# pego novas linhas de texto
		# usa split('\n') para deixar '' no final
		lines = text.split('\n')

		# formata as linhas novas
		lines = [s._format(l) for l in lines]

		if len(s._content) > 0:
			last = s._content.pop(-1)
			# junta  a última linha com a primeira nova
			lines[0] = last + lines[0]

		# adiciona as linhas ao content
		s._content += lines

		# mantém o limite de linhas
		if len(s._content) > s._max:
			s._idx -= len(s._content[s._max:])
			s._content = s._content[-s._max:]

		s._draw_cond.notify()
		s._draw_cond.release()

	def clear(s):
		_, maxwidth = termwin.gettermsize()
		width = s.width if s.column + s.width < maxwidth else s.width - 1
		with termwin._draw_lock:
			print(
					s._setcolors() + \
					termwin._move(
						s.column,
						s.row
						) + ''.join(
							[' ' * s.width + termwin._left(width) + termwin._down()] * s.height
							) + s._resetcolors(),
						end='', flush=True
						)

	def _draw(s):
		s.clear()
		overflow = []

		s._draw_cond.acquire()
		s._draw_cond.notify()
		while not s._die:
			s._draw_cond.wait()
			content = s._content[s._idx:] if '' not in s._content[-1:] else s._content[:-1]
			content = overflow + content
			for line in overflow + content:
				wrapped = s._wraptext(line)
				for l in wrapped:
					with termwin._draw_lock:
						print(
							s._setcolors() + \
							termwin._move(
								s.column,
								s.row + s._offset
								) + l.ljust(s.width) + \
							s._resetcolors(),
							flush=True)
					s._offset += 1
					if s._offset >= s.height:
						overflow = list(wrapped[wrapped.index(l)+1:])
						s._offset = 0
						with s._timeout_cond:
							s._timeout_cond.wait(s.timeout)
						s.clear()
			s._idx = len(s._content)
		s._draw_cond.release()
