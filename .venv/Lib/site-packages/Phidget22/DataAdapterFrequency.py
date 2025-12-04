import sys
import ctypes
class DataAdapterFrequency:
	# 10kHz communication frequency
	FREQUENCY_10kHz = 1
	# 100kHz communication frequency
	FREQUENCY_100kHz = 2
	# 400kHz communication frequency
	FREQUENCY_400kHz = 3
	# 187.5kHz communication frequency
	FREQUENCY_188kHz = 4
	# 375kHz communication frequency
	FREQUENCY_375kHz = 5
	# 750kHz communication frequency
	FREQUENCY_750kHz = 6
	# 1500kHz communication frequency
	FREQUENCY_1500kHz = 7
	# 3MHz communication frequency
	FREQUENCY_3MHz = 8
	# 6MHz communication frequency
	FREQUENCY_6MHz = 9

	@classmethod
	def getName(self, val):
		if val == self.FREQUENCY_10kHz:
			return "FREQUENCY_10kHz"
		if val == self.FREQUENCY_100kHz:
			return "FREQUENCY_100kHz"
		if val == self.FREQUENCY_400kHz:
			return "FREQUENCY_400kHz"
		if val == self.FREQUENCY_188kHz:
			return "FREQUENCY_188kHz"
		if val == self.FREQUENCY_375kHz:
			return "FREQUENCY_375kHz"
		if val == self.FREQUENCY_750kHz:
			return "FREQUENCY_750kHz"
		if val == self.FREQUENCY_1500kHz:
			return "FREQUENCY_1500kHz"
		if val == self.FREQUENCY_3MHz:
			return "FREQUENCY_3MHz"
		if val == self.FREQUENCY_6MHz:
			return "FREQUENCY_6MHz"
		return "<invalid enumeration value>"
