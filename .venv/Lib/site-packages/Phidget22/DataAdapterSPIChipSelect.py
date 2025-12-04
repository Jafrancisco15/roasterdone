import sys
import ctypes
class DataAdapterSPIChipSelect:
	# CS normally HIGH, Automatically goes LOW during transmission
	SPI_CHIP_SELECT_ACTIVE_LOW = 1
	# CS normally LOW, Automatically goes HIGH during transmission
	SPI_CHIP_SELECT_ACTIVE_HIGH = 2
	# CS is held LOW as long as this is set
	SPI_CHIP_SELECT_LOW = 3
	# CS is held HIGH as long as this is set
	SPI_CHIP_SELECT_HIGH = 4

	@classmethod
	def getName(self, val):
		if val == self.SPI_CHIP_SELECT_ACTIVE_LOW:
			return "SPI_CHIP_SELECT_ACTIVE_LOW"
		if val == self.SPI_CHIP_SELECT_ACTIVE_HIGH:
			return "SPI_CHIP_SELECT_ACTIVE_HIGH"
		if val == self.SPI_CHIP_SELECT_LOW:
			return "SPI_CHIP_SELECT_LOW"
		if val == self.SPI_CHIP_SELECT_HIGH:
			return "SPI_CHIP_SELECT_HIGH"
		return "<invalid enumeration value>"
