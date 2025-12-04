import sys
import ctypes
class DriveMode:
	# Configures the motor for coasting deceleration
	DRIVE_MODE_COAST = 1
	# Configures the motor for forced deceleration
	DRIVE_MODE_FORCED = 2

	@classmethod
	def getName(self, val):
		if val == self.DRIVE_MODE_COAST:
			return "DRIVE_MODE_COAST"
		if val == self.DRIVE_MODE_FORCED:
			return "DRIVE_MODE_FORCED"
		return "<invalid enumeration value>"
