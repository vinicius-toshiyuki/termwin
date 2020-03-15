from termwin.window import Window
import termwin
from threading import Thread

class LoopWindow(Window):
	def _draw(s):
		s.clear()
		
		s._draw_cond.acquire()
		s._draw_cond.notify()
		while not s._die:
			s._draw_cond.wait(s.timeout)
			s.clear()
			s._idx = 0
			overflow = []
			offset = 0
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
								s.row + offset
								) + l.ljust(s.width) + \
							s._resetcolors(),
							flush=True)
					if (offset := offset + 1) >= s.height:
						if l != wrapped[-1] or line != content[-1]:
							with s._timeout_cond:
								s._timeout_cond.wait(s.timeout)
							s.clear()
						overflow = list(wrapped[wrapped.index(l)+1:])
						offset = 0
		s._draw_cond.release()
