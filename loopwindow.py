from termwin.window import Window
import termwin
from threading import Thread

class LoopWindow(Window):
	def _draw(s):
		s.clear()
		skip = 0
		
		s._draw_cond.acquire()
		s._draw_cond.notify()
		while not s._die:
			s._draw_cond.wait(s.timeout)
			s.clear()
			s._idx = 0
			s._offset = 0
			content = s._content[s._idx:] if '' not in s._content[-1:] else s._content[:-1]
			for line in content:
				wrapped = s._wraptext(line)[skip:]
				for i, l in enumerate(wrapped):
					if s._offset >= s.height:
						skip = i
						s._offset = 0
						if l != wrapped[0] or line != content[0]:
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
		s._draw_cond.release()
