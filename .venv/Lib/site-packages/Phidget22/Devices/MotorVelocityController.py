import sys
import ctypes
from Phidget22.PhidgetSupport import PhidgetSupport
from Phidget22.Async import *
from Phidget22.PositionType import PositionType
from Phidget22.PhidgetException import PhidgetException

from Phidget22.Phidget import Phidget

class MotorVelocityController(Phidget):

	def __init__(self):
		Phidget.__init__(self)
		self.handle = ctypes.c_void_p()

		if sys.platform == 'win32':
			self._DutyCycleUpdateFactory = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		else:
			self._DutyCycleUpdateFactory = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		self._DutyCycleUpdate = None
		self._onDutyCycleUpdate = None

		if sys.platform == 'win32':
			self._ExpectedVelocityChangeFactory = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		else:
			self._ExpectedVelocityChangeFactory = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		self._ExpectedVelocityChange = None
		self._onExpectedVelocityChange = None

		if sys.platform == 'win32':
			self._VelocityChangeFactory = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		else:
			self._VelocityChangeFactory = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double)
		self._VelocityChange = None
		self._onVelocityChange = None

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_create
		__func.restype = ctypes.c_int32
		res = __func(ctypes.byref(self.handle))

		if res > 0:
			raise PhidgetException(res)

	def __del__(self):
		Phidget.__del__(self)

	def _localDutyCycleUpdateEvent(self, handle, userPtr, dutyCycle):
		if self._DutyCycleUpdate == None:
			return
		self._DutyCycleUpdate(self, dutyCycle)

	def setOnDutyCycleUpdateHandler(self, handler):
		if handler == None:
			self._DutyCycleUpdate = None
			self._onDutyCycleUpdate = None
		else:
			self._DutyCycleUpdate = handler
			self._onDutyCycleUpdate = self._DutyCycleUpdateFactory(self._localDutyCycleUpdateEvent)

		try:
			__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setOnDutyCycleUpdateHandler
			__func.restype = ctypes.c_int32
			res = __func(self.handle, self._onDutyCycleUpdate, None)
		except RuntimeError:
			self._DutyCycleUpdate = None
			self._onDutyCycleUpdate = None

	def _localExpectedVelocityChangeEvent(self, handle, userPtr, expectedVelocity):
		if self._ExpectedVelocityChange == None:
			return
		self._ExpectedVelocityChange(self, expectedVelocity)

	def setOnExpectedVelocityChangeHandler(self, handler):
		if handler == None:
			self._ExpectedVelocityChange = None
			self._onExpectedVelocityChange = None
		else:
			self._ExpectedVelocityChange = handler
			self._onExpectedVelocityChange = self._ExpectedVelocityChangeFactory(self._localExpectedVelocityChangeEvent)

		try:
			__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setOnExpectedVelocityChangeHandler
			__func.restype = ctypes.c_int32
			res = __func(self.handle, self._onExpectedVelocityChange, None)
		except RuntimeError:
			self._ExpectedVelocityChange = None
			self._onExpectedVelocityChange = None

	def _localVelocityChangeEvent(self, handle, userPtr, velocity):
		if self._VelocityChange == None:
			return
		self._VelocityChange(self, velocity)

	def setOnVelocityChangeHandler(self, handler):
		if handler == None:
			self._VelocityChange = None
			self._onVelocityChange = None
		else:
			self._VelocityChange = handler
			self._onVelocityChange = self._VelocityChangeFactory(self._localVelocityChangeEvent)

		try:
			__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setOnVelocityChangeHandler
			__func.restype = ctypes.c_int32
			res = __func(self.handle, self._onVelocityChange, None)
		except RuntimeError:
			self._VelocityChange = None
			self._onVelocityChange = None

	def getAcceleration(self):
		_Acceleration = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getAcceleration
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Acceleration))

		if result > 0:
			raise PhidgetException(result)

		return _Acceleration.value

	def setAcceleration(self, Acceleration):
		_Acceleration = ctypes.c_double(Acceleration)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setAcceleration
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Acceleration)

		if result > 0:
			raise PhidgetException(result)


	def getMinAcceleration(self):
		_MinAcceleration = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinAcceleration
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinAcceleration))

		if result > 0:
			raise PhidgetException(result)

		return _MinAcceleration.value

	def getMaxAcceleration(self):
		_MaxAcceleration = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxAcceleration
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxAcceleration))

		if result > 0:
			raise PhidgetException(result)

		return _MaxAcceleration.value

	def getActiveCurrentLimit(self):
		_ActiveCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getActiveCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_ActiveCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _ActiveCurrentLimit.value

	def getCurrentLimit(self):
		_CurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_CurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _CurrentLimit.value

	def setCurrentLimit(self, CurrentLimit):
		_CurrentLimit = ctypes.c_double(CurrentLimit)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _CurrentLimit)

		if result > 0:
			raise PhidgetException(result)


	def getMinCurrentLimit(self):
		_MinCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _MinCurrentLimit.value

	def getMaxCurrentLimit(self):
		_MaxCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _MaxCurrentLimit.value

	def getDataInterval(self):
		_DataInterval = ctypes.c_uint32()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getDataInterval
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_DataInterval))

		if result > 0:
			raise PhidgetException(result)

		return _DataInterval.value

	def setDataInterval(self, DataInterval):
		_DataInterval = ctypes.c_uint32(DataInterval)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setDataInterval
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _DataInterval)

		if result > 0:
			raise PhidgetException(result)


	def getMinDataInterval(self):
		_MinDataInterval = ctypes.c_uint32()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinDataInterval
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinDataInterval))

		if result > 0:
			raise PhidgetException(result)

		return _MinDataInterval.value

	def getMaxDataInterval(self):
		_MaxDataInterval = ctypes.c_uint32()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxDataInterval
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxDataInterval))

		if result > 0:
			raise PhidgetException(result)

		return _MaxDataInterval.value

	def getDataRate(self):
		_DataRate = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getDataRate
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_DataRate))

		if result > 0:
			raise PhidgetException(result)

		return _DataRate.value

	def setDataRate(self, DataRate):
		_DataRate = ctypes.c_double(DataRate)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setDataRate
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _DataRate)

		if result > 0:
			raise PhidgetException(result)


	def getMinDataRate(self):
		_MinDataRate = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinDataRate
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinDataRate))

		if result > 0:
			raise PhidgetException(result)

		return _MinDataRate.value

	def getMaxDataRate(self):
		_MaxDataRate = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxDataRate
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxDataRate))

		if result > 0:
			raise PhidgetException(result)

		return _MaxDataRate.value

	def getDeadBand(self):
		_DeadBand = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getDeadBand
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_DeadBand))

		if result > 0:
			raise PhidgetException(result)

		return _DeadBand.value

	def setDeadBand(self, DeadBand):
		_DeadBand = ctypes.c_double(DeadBand)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setDeadBand
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _DeadBand)

		if result > 0:
			raise PhidgetException(result)


	def getDutyCycle(self):
		_DutyCycle = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getDutyCycle
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_DutyCycle))

		if result > 0:
			raise PhidgetException(result)

		return _DutyCycle.value

	def getEngaged(self):
		_Engaged = ctypes.c_int()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getEngaged
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Engaged))

		if result > 0:
			raise PhidgetException(result)

		return bool(_Engaged.value)

	def setEngaged(self, Engaged):
		_Engaged = ctypes.c_int(Engaged)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setEngaged
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Engaged)

		if result > 0:
			raise PhidgetException(result)


	def getExpectedVelocity(self):
		_ExpectedVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getExpectedVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_ExpectedVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _ExpectedVelocity.value

	def setEnableExpectedVelocity(self, EnableExpectedVelocity):
		_EnableExpectedVelocity = ctypes.c_int(EnableExpectedVelocity)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setEnableExpectedVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _EnableExpectedVelocity)

		if result > 0:
			raise PhidgetException(result)


	def getEnableExpectedVelocity(self):
		_EnableExpectedVelocity = ctypes.c_int()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getEnableExpectedVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_EnableExpectedVelocity))

		if result > 0:
			raise PhidgetException(result)

		return bool(_EnableExpectedVelocity.value)

	def enableFailsafe(self, failsafeTime):
		_failsafeTime = ctypes.c_uint32(failsafeTime)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_enableFailsafe
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _failsafeTime)

		if result > 0:
			raise PhidgetException(result)


	def getFailsafeBrakingEnabled(self):
		_FailsafeBrakingEnabled = ctypes.c_int()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getFailsafeBrakingEnabled
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_FailsafeBrakingEnabled))

		if result > 0:
			raise PhidgetException(result)

		return bool(_FailsafeBrakingEnabled.value)

	def setFailsafeBrakingEnabled(self, FailsafeBrakingEnabled):
		_FailsafeBrakingEnabled = ctypes.c_int(FailsafeBrakingEnabled)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setFailsafeBrakingEnabled
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _FailsafeBrakingEnabled)

		if result > 0:
			raise PhidgetException(result)


	def getFailsafeCurrentLimit(self):
		_FailsafeCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getFailsafeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_FailsafeCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _FailsafeCurrentLimit.value

	def setFailsafeCurrentLimit(self, FailsafeCurrentLimit):
		_FailsafeCurrentLimit = ctypes.c_double(FailsafeCurrentLimit)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setFailsafeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _FailsafeCurrentLimit)

		if result > 0:
			raise PhidgetException(result)


	def getMinFailsafeTime(self):
		_MinFailsafeTime = ctypes.c_uint32()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinFailsafeTime
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinFailsafeTime))

		if result > 0:
			raise PhidgetException(result)

		return _MinFailsafeTime.value

	def getMaxFailsafeTime(self):
		_MaxFailsafeTime = ctypes.c_uint32()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxFailsafeTime
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxFailsafeTime))

		if result > 0:
			raise PhidgetException(result)

		return _MaxFailsafeTime.value

	def getInductance(self):
		_Inductance = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getInductance
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Inductance))

		if result > 0:
			raise PhidgetException(result)

		return _Inductance.value

	def setInductance(self, Inductance):
		_Inductance = ctypes.c_double(Inductance)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setInductance
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Inductance)

		if result > 0:
			raise PhidgetException(result)


	def getMinInductance(self):
		_MinInductance = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinInductance
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinInductance))

		if result > 0:
			raise PhidgetException(result)

		return _MinInductance.value

	def getMaxInductance(self):
		_MaxInductance = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxInductance
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxInductance))

		if result > 0:
			raise PhidgetException(result)

		return _MaxInductance.value

	def getKd(self):
		_Kd = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getKd
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Kd))

		if result > 0:
			raise PhidgetException(result)

		return _Kd.value

	def setKd(self, Kd):
		_Kd = ctypes.c_double(Kd)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setKd
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Kd)

		if result > 0:
			raise PhidgetException(result)


	def getKi(self):
		_Ki = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getKi
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Ki))

		if result > 0:
			raise PhidgetException(result)

		return _Ki.value

	def setKi(self, Ki):
		_Ki = ctypes.c_double(Ki)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setKi
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Ki)

		if result > 0:
			raise PhidgetException(result)


	def getKp(self):
		_Kp = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getKp
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Kp))

		if result > 0:
			raise PhidgetException(result)

		return _Kp.value

	def setKp(self, Kp):
		_Kp = ctypes.c_double(Kp)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setKp
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _Kp)

		if result > 0:
			raise PhidgetException(result)


	def getPositionType(self):
		_PositionType = ctypes.c_int()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getPositionType
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_PositionType))

		if result > 0:
			raise PhidgetException(result)

		return _PositionType.value

	def setPositionType(self, PositionType):
		_PositionType = ctypes.c_int(PositionType)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setPositionType
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _PositionType)

		if result > 0:
			raise PhidgetException(result)


	def getRescaleFactor(self):
		_RescaleFactor = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getRescaleFactor
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_RescaleFactor))

		if result > 0:
			raise PhidgetException(result)

		return _RescaleFactor.value

	def setRescaleFactor(self, RescaleFactor):
		_RescaleFactor = ctypes.c_double(RescaleFactor)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setRescaleFactor
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _RescaleFactor)

		if result > 0:
			raise PhidgetException(result)


	def resetFailsafe(self):
		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_resetFailsafe
		__func.restype = ctypes.c_int32
		result = __func(self.handle)

		if result > 0:
			raise PhidgetException(result)


	def getStallVelocity(self):
		_StallVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getStallVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_StallVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _StallVelocity.value

	def setStallVelocity(self, StallVelocity):
		_StallVelocity = ctypes.c_double(StallVelocity)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setStallVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _StallVelocity)

		if result > 0:
			raise PhidgetException(result)


	def getMinStallVelocity(self):
		_MinStallVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinStallVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinStallVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _MinStallVelocity.value

	def getMaxStallVelocity(self):
		_MaxStallVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxStallVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxStallVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _MaxStallVelocity.value

	def getSurgeCurrentLimit(self):
		_SurgeCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getSurgeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_SurgeCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _SurgeCurrentLimit.value

	def setSurgeCurrentLimit(self, SurgeCurrentLimit):
		_SurgeCurrentLimit = ctypes.c_double(SurgeCurrentLimit)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setSurgeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _SurgeCurrentLimit)

		if result > 0:
			raise PhidgetException(result)


	def getMinSurgeCurrentLimit(self):
		_MinSurgeCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinSurgeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinSurgeCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _MinSurgeCurrentLimit.value

	def getMaxSurgeCurrentLimit(self):
		_MaxSurgeCurrentLimit = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxSurgeCurrentLimit
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxSurgeCurrentLimit))

		if result > 0:
			raise PhidgetException(result)

		return _MaxSurgeCurrentLimit.value

	def getTargetVelocity(self):
		_TargetVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getTargetVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_TargetVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _TargetVelocity.value

	def setTargetVelocity(self, TargetVelocity):
		_TargetVelocity = ctypes.c_double(TargetVelocity)

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_setTargetVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, _TargetVelocity)

		if result > 0:
			raise PhidgetException(result)


	def getMinTargetVelocity(self):
		_MinTargetVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMinTargetVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MinTargetVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _MinTargetVelocity.value

	def getMaxTargetVelocity(self):
		_MaxTargetVelocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getMaxTargetVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_MaxTargetVelocity))

		if result > 0:
			raise PhidgetException(result)

		return _MaxTargetVelocity.value

	def getVelocity(self):
		_Velocity = ctypes.c_double()

		__func = PhidgetSupport.getDll().PhidgetMotorVelocityController_getVelocity
		__func.restype = ctypes.c_int32
		result = __func(self.handle, ctypes.byref(_Velocity))

		if result > 0:
			raise PhidgetException(result)

		return _Velocity.value
