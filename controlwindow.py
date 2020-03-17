from termwin.window import Window
import termwin as tw
from threading import Thread, Condition

class ControlWindow(Window):
	def __init__(s, *args, **kwargs):
		s.print = None
		s.input = None
		s.wipe = None
		s._paused_cond = Condition()
		s._running_cond = Condition()
		s._control_t = Thread(target=s._control)
		super().__init__(*args, **kwargs)

	def die(s):
		super().die()
		if s._control_t.is_alive():
			s._control_t.join()

	def start(s, ch='0'):
		tw.readchar(True)
		s.ch = ch[0] if len(ch) > 0 else '0'
		s._running = True
		s._paused = False
		s._control_t.start()
	def pause(s):
		with s._paused_cond:
			s._paused = True
		tw.readchar(True)
	def resume(s):
		tw.readchar(True)
		with s._paused_cond:
			s._paused = False
			s._paused_cond.notify()
	def stop(s):
		with s._running_cond:
			s._running = False
			s.resume()
			s._running_cond.notify()
		tw.readchar(True)

	def _control(s):
		bounds = (s.row,s.column,s.row+s.height,s.column+s.width)
		row = bounds[0]
		col = bounds[1]
		with tw._draw_lock:
			print(tw._move(int(col), int(row)), end='', flush=True)
			print(s._setcolors() + s.ch + s._resetcolors(), end='', flush=True)
		with s._running_cond:
			while s._running:
				s._paused_cond.acquire()
				while s._paused:
					s._paused_cond.wait()
				s._paused_cond.release()
				c = tw.readchar()
				with tw._draw_lock:
					print(tw._move(int(col), int(row)), end='', flush=True)
					print(s._setcolors() + ' ' + s._resetcolors(), end='', flush=True)
					if c == tw.up and row > bounds[0]:
						row -= 1
					if c == tw.down and row < bounds[2]:
						row += 1
					if c == tw.right and col < bounds[3]:
						col += 1
					if c == tw.left and col > bounds[1]:
						col -= 1
					print(tw._move(int(col), int(row)), end='', flush=True)
					print(s._setcolors() + s.ch + s._resetcolors(), end='', flush=True)
				s._running_cond.wait(1/24)
