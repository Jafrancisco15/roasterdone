import sys
import ctypes
class RFIDProtocol:
	# EM4100 Series
	PROTOCOL_EM4100 = 1
	# ISO11785 FDX B
	PROTOCOL_ISO11785_FDX_B = 2
	# PhidgetTAG
	PROTOCOL_PHIDGETS = 3
	# HID Generic
	PROTOCOL_HID_GENERIC = 4
	# HID H10301
	PROTOCOL_HID_H10301 = 5

	@classmethod
	def getName(self, val):
		if val == self.PROTOCOL_EM4100:
			return "PROTOCOL_EM4100"
		if val == self.PROTOCOL_ISO11785_FDX_B:
			return "PROTOCOL_ISO11785_FDX_B"
		if val == self.PROTOCOL_PHIDGETS:
			return "PROTOCOL_PHIDGETS"
		if val == self.PROTOCOL_HID_GENERIC:
			return "PROTOCOL_HID_GENERIC"
		if val == self.PROTOCOL_HID_H10301:
			return "PROTOCOL_HID_H10301"
		return "<invalid enumeration value>"
