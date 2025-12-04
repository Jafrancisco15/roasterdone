import time, threading, math, collections

class ETReader:
    def __init__(self, sample_hz=2.0, channel=0, thermocouple_type="K",
                 force_sim=False, force_phidget=False):
        self.set_rate(sample_hz)
        self.et_c = float('nan')
        self.raw_c = float('nan')
        self.last_update = 0.0
        self.ok = False
        self.source = "Simulador"
        self.warn = ""
        self._stop = threading.Event()
        self._use_sim = force_sim
        self._force_phidget = force_phidget
        self.channel = int(channel)
        self.thermocouple_type = str(thermocouple_type).upper()
        self._dq = collections.deque(maxlen=7)
        self._ambient_monitor = collections.deque(maxlen=16)
        self._ts = None
        if not self._use_sim:
            try:
                from Phidget22.Devices.TemperatureSensor import TemperatureSensor
                from Phidget22.ThermocoupleType import ThermocoupleType
                self._ts = TemperatureSensor()
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
                self.ok = True; self.source="Phidget"
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
                # Roast-like simulator: ET starts high at charge, small drop, then ramps
                if not hasattr(self, '_t0_sim'):
                    self._t0_sim = time.time()
                elapsed = time.time() - self._t0_sim
                # Phases (seconds): 0-30 preheat to ~200C, 30-60 charge drop to ~170C, 60-540 ramp to ~230C, then hold
                if elapsed < 30.0:
                    base = 180.0 + (200.0-180.0)*(elapsed/30.0)
                elif elapsed < 60.0:
                    base = 200.0 - (200.0-170.0)*((elapsed-30.0)/30.0)
                elif elapsed < 540.0:
                    base = 170.0 + (230.0-170.0)*((elapsed-60.0)/(480.0))
                else:
                    base = 230.0 + 2.0*math.sin(elapsed/15.0)
                ripple = 0.6*math.sin(elapsed/7.0) + 0.3*math.sin(elapsed/3.3)
                raw = base + ripple
                self.raw_c = raw
                self.et_c = self._smooth(raw)
                self.last_update = time.time()
                self.ok = True
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
                    self.last_update = now
                    self.ok = True; self.source="Phidget"
                except Exception:
                    self.ok = False; self.source="Phidget?"
                    self.raw_c = float('nan')
                    self.et_c = float('nan')
                    self.last_update = 0.0
            time.sleep(self.sample_dt)
