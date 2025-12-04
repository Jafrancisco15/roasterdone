import time, threading, math, collections


def _clean_serial(value):
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return int(value)
    except Exception:
        return None

class ETReader:
    def __init__(self, sample_hz=2.0, channel=0, thermocouple_type="K",
                 force_sim=False, force_phidget=False, device_serial=None):
        self.set_rate(sample_hz)
        self.et_c = float('nan')
        self.raw_c = float('nan')
        self.ok = False
        self.source = "Simulador"
        self.warn = ""
        self._stop = threading.Event()
        self._use_sim = force_sim
        self._force_phidget = force_phidget
        self.channel = int(channel)
        self.thermocouple_type = str(thermocouple_type).upper()
        self.device_serial = _clean_serial(device_serial)
        self._dq = collections.deque(maxlen=7)
        self._ambient_monitor = collections.deque(maxlen=16)
        self._ts = None
        if not self._use_sim:
            try:
                from Phidget22.Devices.TemperatureSensor import TemperatureSensor
                from Phidget22.ThermocoupleType import ThermocoupleType
                from Phidget22.DeviceID import DeviceID
                self._ts = TemperatureSensor()
                if self.device_serial is not None:
                    try:
                        self._ts.setDeviceSerialNumber(self.device_serial)
                    except Exception:
                        pass
                self._ts.setChannel(self.channel)
                self._ts.openWaitForAttachment(3000)
                try:
                    self._ts.setTemperatureChangeTrigger(0.0)
                except Exception: pass
                try:
                    self._ts.setDataInterval(int(1000*self.sample_dt))
                except Exception: pass
                try:
                    tc_map = {
                        "K": ThermocoupleType.THERMOCOUPLE_TYPE_K,
                        "J": ThermocoupleType.THERMOCOUPLE_TYPE_J,
                        "E": ThermocoupleType.THERMOCOUPLE_TYPE_E,
                        "T": ThermocoupleType.THERMOCOUPLE_TYPE_T,
                        "N": ThermocoupleType.THERMOCOUPLE_TYPE_N,
                        "S": ThermocoupleType.THERMOCOUPLE_TYPE_S,
                        "R": ThermocoupleType.THERMOCOUPLE_TYPE_R,
                        "B": ThermocoupleType.THERMOCOUPLE_TYPE_B,
                    }
                    self._ts.setThermocoupleType(tc_map.get(self.thermocouple_type, ThermocoupleType.THERMOCOUPLE_TYPE_K))
                except Exception: pass
                try:
                    dev_id = self._ts.getDeviceID()
                    if dev_id == DeviceID.PHIDID_TEMPERATURESENSOR_4:
                        self.source = "Phidget 1048"
                    else:
                        self.source = f"Phidget ({dev_id})"
                        self.warn = "Phidget detectado no es 1048"
                except Exception:
                    self.source = "Phidget"
                self.ok = True
            except Exception:
                if self._force_phidget:
                    raise
                self._use_sim = True
                self.ok = False; self.source="Simulador"
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def set_rate(self, sample_hz):
        self.sample_dt = 1.0 / max(0.2, float(sample_hz))

    def start(self):
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            if self._ts is not None:
                self._ts.close()
        except Exception:
            pass

    def _smooth(self, val):
        import statistics
        self._dq.append(val)
        try:
            return statistics.median(self._dq)
        except Exception:
            return val

    def _loop(self):
        last_val = None
        freeze_until = 0.0
        while not self._stop.is_set():
            if self._use_sim:
                t = time.time()
                base = 24 + 100 * (1 - math.exp(-(t%9999)/140.0))
                ripple = 0.4 * math.sin(t/5.0) + 0.15 * math.sin(t/1.7)
                raw = base + ripple
                self.raw_c = raw
                self.et_c = self._smooth(raw)
                self.ok = False
            else:
                try:
                    raw = self._ts.getTemperature()
                    self.raw_c = raw
                    if raw < -10 or raw > 350:
                        raw = float('nan')
                    if last_val is None:
                        last_val = raw
                    else:
                        dv = raw - last_val
                        if self._ambient_monitor and max(self._ambient_monitor) < 40.0:
                            if abs(dv) > 2.0:
                                raw = last_val + (2.0 if dv>0 else -2.0)
                        last_val = raw
                    now = time.time()
                    self._ambient_monitor.append(raw)
                    if len(self._ambient_monitor) >= 8:
                        span = len(self._ambient_monitor)*self.sample_dt
                        delta = self._ambient_monitor[-1] - self._ambient_monitor[0]
                        slope = delta / max(1e-6, span)
                        if max(self._ambient_monitor) < 40.0 and slope > 0.5 and now > freeze_until:
                            med = self._smooth(raw)
                            self.et_c = med
                            self.warn = "Drift ambiente: congelando 5s"
                            freeze_until = now + 5.0
                        else:
                            self.warn = ""
                    if now >= freeze_until:
                        self.et_c = self._smooth(raw)
                    if not str(self.source).lower().startswith("phidget"):
                        self.source = "Phidget"
                    self.ok = True
                except Exception:
                    self.ok = False; self.source="Phidget?"
            time.sleep(self.sample_dt)
