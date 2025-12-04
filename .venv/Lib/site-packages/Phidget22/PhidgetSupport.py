import threading
import sys
import ctypes
from ctypes import *
import os

class PhidgetSupport:
	__dll = None

	@staticmethod
	def getDll():
		if PhidgetSupport.__dll is None:
			libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".libs")
			if sys.platform == 'win32':
				if os.path.exists(os.path.join(libs_path, "phidget22.dll")):
					PhidgetSupport.__dll = windll.LoadLibrary(os.path.join(libs_path, "phidget22.dll"))
				else:
					PhidgetSupport.__dll = windll.LoadLibrary("phidget22.dll")
			elif sys.platform == 'darwin':
				if os.path.exists(os.path.join(libs_path, "libphidget22.dylib")):
					PhidgetSupport.__dll = cdll.LoadLibrary(os.path.join(libs_path, "libphidget22.dylib"))
				else:
					PhidgetSupport.__dll = cdll.LoadLibrary("libphidget22.dylib")
			else:
				if os.path.exists(os.path.join(libs_path, "libphidget22.so")):
					PhidgetSupport.__dll = cdll.LoadLibrary(os.path.join(libs_path, "libphidget22.so"))
				else:
					PhidgetSupport.__dll = cdll.LoadLibrary("libphidget22.so.0")
		return PhidgetSupport.__dll

	def __init__(self):
		self.handle = None

	def __del__(self):
		pass

	@staticmethod
	def versionChecked_ord(character):
		if(sys.version_info[0] < 3):
			return character
		else:
			return ord(character)
