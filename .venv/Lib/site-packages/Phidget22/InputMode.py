import sys
import ctypes
class InputMode:
	# For interfacing NPN digital sensors
	INPUT_MODE_NPN = 1
	# For interfacing PNP digital sensors
	INPUT_MODE_PNP = 2
	# Floating input
	INPUT_MODE_FLOATING = 3
	# Enables a pullup for interfaces that only pull low
	INPUT_MODE_PULLUP = 4

	@classmethod
	def getName(self, val):
		if val == self.INPUT_MODE_NPN:
			return "INPUT_MODE_NPN"
		if val == self.INPUT_MODE_PNP:
			return "INPUT_MODE_PNP"
		if val == self.INPUT_MODE_FLOATING:
			return "INPUT_MODE_FLOATING"
		if val == self.INPUT_MODE_PULLUP:
			return "INPUT_MODE_PULLUP"
		return "<invalid enumeration value>"
