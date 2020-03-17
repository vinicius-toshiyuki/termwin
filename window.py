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
		text = text.replace('\x02', '')
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

	def _put(s, text):
		s._draw_cond.acquire()

	 	# pego novas linhas de texto
		# usa split('\n') para deixar '' no final
		lines = text.split('\n')

		if len(s._content) > 0:
			last = s._content.pop(-1)
			with termwin._draw_lock:
				for i, l in enumerate(s._wraptext(last)):
					print(s._setcolors() + termwin._move(s.column, s.row + s._offset + i) + ' ' * s.width + s._resetcolors(), end='')
			# junta  a última linha com a primeira nova
			lines[0] = last + lines[0]

		# formata as linhas novas
		lines = [s._format(l) for l in lines]

		# adiciona as linhas ao content
		s._content += lines

		# mantém o limite de linhas
		if len(s._content) > s._max:
			s._idx -= len(s._content[s._max:])
			s._content = s._content[-s._max:]

		s._draw_cond.notify()
		s._draw_cond.release()

	def print(s, *objects, end='\n', sep=' '):
		if end is None:
			end = '\n'
		if sep is None:
			sep = ' '
		objects = list(map(lambda x: str(x), objects))
		text = sep.join(objects) + end
		s._put(text)

	def input(s, prompt=None):
		text = ''
		if prompt:
			s._put(prompt+'\x02')
		while (c := termwin.readchar()) != '\n':
			if ord(c) == 127 or ord(c) == 8:
				text = text[:-1]
				c = '\b'
			elif c.isprintable():
				text += c
			else:
				c = ''
			s._put(c)
		s._put('\n')
		return text

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
		lastoffset = 0
		skip = 0

		s._draw_cond.acquire()
		s._draw_cond.notify()
		while not s._die:
			s._draw_cond.wait()
			# acho que é aqui que tem que mexer para poder usar w.print()
			# pode usar outro caractere de controle tipo \x03 ↓
			content = s._content[s._idx:] #parece que tirando isso dá certo? -> if '' not in s._content[-1:] else s._content[s._idx:-1]
			for line in content:
				wrapped = s._wraptext(line)[skip:]
				lastoffset = len(wrapped)
				for i, l in enumerate(wrapped):
					if s._offset >= s.height:
						skip = i
						s._offset = 0
						with s._timeout_cond:
							s._timeout_cond.wait(s.timeout)
						s.clear()
					with termwin._draw_lock:
						print(
							s._setcolors() + \
							termwin._move(
								s.column,
								s.row + s._offset
								) + l.ljust(s.width) + \
							s._resetcolors(),
							flush=True, end='')
					s._offset += 1
				skip = 0
			s._idx = max(len(s._content) - 1, 0)
			s._offset = max(s._offset - lastoffset, 0)
		s._draw_cond.release()
