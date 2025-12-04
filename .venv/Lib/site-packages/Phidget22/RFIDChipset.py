import sys
import ctypes
class RFIDChipset:
	# T5577
	CHIPSET_T5577 = 1
	# EM4305
	CHIPSET_EM4305 = 2

	@classmethod
	def getName(self, val):
		if val == self.CHIPSET_T5577:
			return "CHIPSET_T5577"
		if val == self.CHIPSET_EM4305:
			return "CHIPSET_EM4305"
		return "<invalid enumeration value>"
