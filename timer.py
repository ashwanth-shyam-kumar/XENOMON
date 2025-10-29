from pygame.time import get_ticks
#get_ticks returns the number of milliseconds passed since the game was initialised
class Timer:
	def __init__(self, duration, repeat = False, autostart = False, func = None):
		self.duration = duration
		self.start_time = 0
		self.active = False
		self.repeat = repeat #to start the timer automatically when it ends
		self.func = func
		if autostart: #whether to start immediately on creation
			self.activate()

	def activate(self):
		self.active = True
		self.start_time = get_ticks()

	def deactivate(self):
		self.active = False
		self.start_time = 0
		if self.repeat: #restart the timer if repeat is true
			self.activate()

	def update(self):
		if self.active:
			current_time = get_ticks()
			if current_time - self.start_time >= self.duration: #when timer duration runs out
				if self.func: self.func() #callback to the function to see what to do next
				self.deactivate()
